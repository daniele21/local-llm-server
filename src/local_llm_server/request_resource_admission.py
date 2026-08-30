"""HTTP transient-memory admission for active inference requests.

Canonical request policy prepares the backend-neutral request first. Optional
queue admission may then delay it. This middleware runs only once the request is
actually ready to enter the route, reserves transient memory in the same global
ResourceManager ledger as resident runtimes, and retains that reservation until
a streaming body is fully consumed or cancelled.
"""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .core.contracts import ErrorCode
from .memory_envelope import MemoryEnvelope, request_memory_envelope
from .resource_manager import AdmissionDecision, ReservationKind, ResourceManager

_INFERENCE_PATHS = frozenset({"/v1/chat/completions", "/api/v1/chat"})
_RESOURCE_HEADER = "x-local-llm-transient-reserved-bytes"


def install_request_resource_admission(application: FastAPI) -> FastAPI:
    """Install active-request resource admission exactly once."""
    if getattr(application.state, "request_resource_admission_installed", False):
        return application
    application.state.request_resource_admission_installed = True

    @application.middleware("http")
    async def request_resource_admission(request: Request, call_next):
        if request.method.upper() != "POST" or request.url.path not in _INFERENCE_PATHS:
            return await call_next(request)

        prepared = getattr(request.state, "prepared_inference_request", None)
        canonical = getattr(prepared, "canonical", None)
        manager = getattr(request.app.state, "runtime_manager", None)
        if canonical is None or manager is None:
            return await call_next(request)

        try:
            runtime = manager.resolve(canonical.model)
        except LookupError:
            return await call_next(request)

        envelope = request_memory_envelope(canonical, runtime.cfg)
        resource_manager: ResourceManager | None = manager.resource_manager
        estimate_bytes = envelope.accounted_bytes
        if resource_manager is None or estimate_bytes is None:
            request.state.transient_resource_admission = _metadata(
                envelope,
                decision="unknown",
                reason="resource manager not configured or no transient estimate",
            )
            return await call_next(request)

        reservation_id = f"request:{runtime.key}:{uuid.uuid4().hex}"
        result = resource_manager.reserve(
            reservation_id,
            estimate_bytes,
            kind=ReservationKind.TRANSIENT,
        )
        if result.decision is AdmissionDecision.REJECT:
            request.state.transient_resource_admission = _metadata(
                envelope,
                decision="reject",
                reason=result.reason,
            )
            return _resource_rejected_response(result, envelope)
        if result.decision is AdmissionDecision.UNKNOWN:
            request.state.transient_resource_admission = _metadata(
                envelope,
                decision="unknown",
                reason=result.reason,
            )
            return await call_next(request)

        committed = resource_manager.commit(reservation_id)
        if committed.decision is AdmissionDecision.REJECT:
            resource_manager.release(reservation_id)
            request.state.transient_resource_admission = _metadata(
                envelope,
                decision="reject",
                reason=committed.reason,
            )
            return _resource_rejected_response(committed, envelope)

        request.state.transient_resource_admission = _metadata(
            envelope,
            decision="admit",
            reason=committed.reason,
            reservation_id=reservation_id,
        )
        try:
            response = await call_next(request)
        except asyncio.CancelledError:
            resource_manager.release(reservation_id)
            raise
        except Exception:
            resource_manager.release(reservation_id)
            raise

        response.headers[_RESOURCE_HEADER] = str(estimate_bytes)
        if canonical.stream is True and hasattr(response, "body_iterator"):
            response.body_iterator = _hold_reservation_for_stream(
                response.body_iterator,
                resource_manager=resource_manager,
                reservation_id=reservation_id,
            )
            return response

        resource_manager.release(reservation_id)
        return response

    return application


async def _hold_reservation_for_stream(
    source: AsyncIterator[Any],
    *,
    resource_manager: ResourceManager,
    reservation_id: str,
) -> AsyncIterator[Any]:
    try:
        async for chunk in source:
            yield chunk
    finally:
        resource_manager.release(reservation_id)


def _resource_rejected_response(result: Any, envelope: MemoryEnvelope) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "code": ErrorCode.RESOURCE_EXHAUSTED.value,
                "message": "active request exceeds configured usable memory budget",
                "retryable": True,
                "details": {
                    "requested_bytes": result.requested_bytes,
                    "committed_bytes": result.committed_bytes,
                    "reserved_bytes": result.reserved_bytes,
                    "usable_budget_bytes": result.usable_budget_bytes,
                    "envelope_complete": envelope.complete,
                    "unavailable_components": list(envelope.unavailable_components),
                },
            }
        },
    )


def _metadata(
    envelope: MemoryEnvelope,
    *,
    decision: str,
    reason: str,
    reservation_id: str | None = None,
) -> dict[str, Any]:
    metadata = envelope.as_dict()
    metadata.update(
        {
            "decision": decision,
            "reason": reason,
            "reservation_id": reservation_id,
        }
    )
    return metadata
