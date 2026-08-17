"""Product HTTP request admission before runtime leases.

The middleware consumes the canonical request prepared by request policy, then
queues per resident runtime. It does not replace backend batching or the final
runtime semaphore. Streaming requests keep their scheduler slot until the body
iterator finishes.
"""
from __future__ import annotations

import asyncio
import threading
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .async_scheduler import AsyncRuntimeGate
from .core.contracts import ErrorCode, InferenceError
from .live_evidence import record_runtime_metrics
from .metrics import DurationMetrics, InferenceMetrics
from .request_pipeline import public_error_detail
from .scheduler_policy import RequestSchedulerSettings, scheduler_settings_from_env

_INFERENCE_PATHS = frozenset({"/v1/chat/completions", "/api/v1/chat"})
_QUEUE_WAIT_HEADER = "x-local-llm-queue-wait-ms"


@dataclass(slots=True)
class _GateEntry:
    runtime: Any
    gate: AsyncRuntimeGate


class RuntimeGateRegistry:
    """Own one admission gate per current runtime residency."""

    def __init__(self, settings: RequestSchedulerSettings) -> None:
        if not settings.enabled or settings.queue_capacity is None:
            raise ValueError("runtime gate registry requires enabled queue settings")
        self.settings = settings
        self._entries: dict[str, _GateEntry] = {}
        self._lock = threading.RLock()

    def gate_for(self, runtime: Any) -> AsyncRuntimeGate:
        with self._lock:
            existing = self._entries.get(runtime.key)
            if existing is not None and existing.runtime is runtime:
                return existing.gate
            gate = AsyncRuntimeGate(
                capacity=int(self.settings.queue_capacity),
                max_running=max(1, int(runtime.cfg.get("max_concurrent_requests") or 1)),
            )
            self._entries[runtime.key] = _GateEntry(runtime=runtime, gate=gate)
            return gate

    def entry_count(self) -> int:
        with self._lock:
            return len(self._entries)


async def _safe_forget(gate: AsyncRuntimeGate, request_id: str) -> None:
    try:
        await gate.forget(request_id)
    except (KeyError, RuntimeError):
        pass


def install_request_scheduler(
    application: FastAPI,
    *,
    settings: RequestSchedulerSettings | None = None,
) -> FastAPI:
    """Install opt-in queue admission exactly once."""
    if getattr(application.state, "request_scheduler_installed", False):
        return application
    application.state.request_scheduler_installed = True

    resolved = settings or scheduler_settings_from_env()
    application.state.request_scheduler_settings = resolved
    if not resolved.enabled:
        application.state.runtime_gate_registry = None
        return application

    registry = RuntimeGateRegistry(resolved)
    application.state.runtime_gate_registry = registry

    @application.middleware("http")
    async def request_scheduler(request: Request, call_next):
        if request.method.upper() != "POST" or request.url.path not in _INFERENCE_PATHS:
            return await call_next(request)

        prepared = getattr(request.state, "prepared_inference_request", None)
        canonical = getattr(prepared, "canonical", None)
        manager = getattr(request.app.state, "runtime_manager", None)
        if canonical is None or manager is None:
            return await call_next(request)

        try:
            timeout_seconds = resolved.timeout_seconds_for_headers(request.headers)
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": {
                        "code": ErrorCode.INVALID_REQUEST.value,
                        "message": str(exc),
                        "retryable": False,
                        "details": {},
                    }
                },
            )

        base_request_id = uuid.uuid4().hex
        for attempt in range(2):
            try:
                runtime = manager.resolve(canonical.model)
            except LookupError:
                return await call_next(request)

            gate = registry.gate_for(runtime)
            request_id = f"{base_request_id}-{attempt}"
            try:
                scheduled = await gate.acquire(
                    request_id,
                    canonical,
                    timeout_seconds=timeout_seconds,
                )
            except InferenceError as exc:
                await _safe_forget(gate, request_id)
                return _scheduler_error_response(exc)
            except asyncio.CancelledError:
                await _safe_forget(gate, request_id)
                raise

            queue_wait_ms = max(
                0.0,
                ((scheduled.started_at or scheduled.admitted_at or scheduled.submitted_at) - scheduled.submitted_at)
                * 1000.0,
            )

            try:
                current_runtime = manager.resolve(canonical.model)
            except LookupError:
                current_runtime = None
            if current_runtime is not runtime:
                await gate.release(request_id, cancel_requested=True)
                await _safe_forget(gate, request_id)
                if attempt == 0:
                    continue
                return JSONResponse(
                    status_code=409,
                    content={
                        "detail": {
                            "code": ErrorCode.MODEL_NOT_RESIDENT.value,
                            "message": "runtime residency changed while request was queued; retry request",
                            "retryable": True,
                            "details": {"model": canonical.model},
                        }
                    },
                )

            request.state.queue_wait_ms = queue_wait_ms
            request.state.scheduler_request_id = request_id
            try:
                response = await call_next(request)
            except asyncio.CancelledError:
                await gate.release(request_id, cancel_requested=True)
                await _safe_forget(gate, request_id)
                raise
            except Exception:
                await gate.release(request_id, cancel_requested=True)
                await _safe_forget(gate, request_id)
                raise

            response.headers[_QUEUE_WAIT_HEADER] = f"{queue_wait_ms:.3f}"
            if canonical.stream is True and hasattr(response, "body_iterator"):
                response.body_iterator = _hold_gate_for_stream(
                    response.body_iterator,
                    gate=gate,
                    request_id=request_id,
                )
                return response

            await gate.release(request_id)
            await _safe_forget(gate, request_id)
            record_runtime_metrics(
                runtime,
                InferenceMetrics(
                    durations=DurationMetrics(queue_wait_ms=queue_wait_ms),
                    sources={"queue_wait_ms": "request_scheduler.admission_wall_clock"},
                ),
            )
            return response

        raise RuntimeError("request scheduler exhausted residency retry loop")

    return application


async def _hold_gate_for_stream(
    iterator,
    *,
    gate: AsyncRuntimeGate,
    request_id: str,
):
    cancelled = False
    try:
        async for chunk in iterator:
            yield chunk
    except asyncio.CancelledError:
        cancelled = True
        raise
    finally:
        await gate.release(request_id, cancel_requested=cancelled)
        await _safe_forget(gate, request_id)


def _scheduler_error_response(error: InferenceError) -> JSONResponse:
    status_code = 400
    if error.code is ErrorCode.RESOURCE_EXHAUSTED:
        status_code = 429
    elif error.code is ErrorCode.TIMEOUT:
        status_code = 408
    elif error.code is ErrorCode.CANCELLED:
        status_code = 409
    return JSONResponse(
        status_code=status_code,
        content={"detail": public_error_detail(error)},
    )
