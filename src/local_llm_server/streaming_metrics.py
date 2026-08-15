"""Truthful HTTP-stream timing for canonical inference requests.

TTFT here is measured at the product HTTP boundary: request receipt to the
first non-empty model content delta emitted by the SSE stream. Role-only events,
empty deltas and ``[DONE]`` do not count as first output.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request

from .live_evidence import record_runtime_metrics
from .metrics import DurationMetrics, InferenceMetrics

_INFERENCE_PATHS = frozenset({"/v1/chat/completions", "/api/v1/chat"})


@dataclass
class StreamTimingRecorder:
    """Incrementally observe SSE chunks without retaining generated content."""

    started_at: float
    clock: Callable[[], float] = time.perf_counter
    first_output_at: float | None = None
    _line_buffer: str = field(default="", init=False, repr=False)

    def observe(self, chunk: bytes | str) -> bool:
        text = chunk.decode("utf-8", errors="replace") if isinstance(chunk, bytes) else str(chunk)
        self._line_buffer += text
        observed = False
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            if self._observe_line(line):
                observed = True
        return observed

    def finish(self, *, completed: bool) -> InferenceMetrics | None:
        if self._line_buffer:
            self._observe_line(self._line_buffer)
            self._line_buffer = ""

        finished_at = self.clock()
        if self.first_output_at is None and not completed:
            return None

        ttft_ms = (
            (self.first_output_at - self.started_at) * 1000.0
            if self.first_output_at is not None
            else None
        )
        total_ms = (finished_at - self.started_at) * 1000.0 if completed else None
        sources: dict[str, str] = {}
        if ttft_ms is not None:
            sources["ttft_ms"] = "http_stream.first_content_delta_wall_clock"
        if total_ms is not None:
            sources["total_ms"] = "http_stream.completed_body_wall_clock"

        return InferenceMetrics(
            durations=DurationMetrics(ttft_ms=ttft_ms, total_ms=total_ms),
            sources=sources,
        )

    def _observe_line(self, line: str) -> bool:
        if self.first_output_at is not None:
            return False
        if not _sse_line_has_model_output(line):
            return False
        self.first_output_at = self.clock()
        return True


def install_streaming_metrics(application: FastAPI) -> FastAPI:
    """Install first-output timing on canonical streaming chat requests."""
    if getattr(application.state, "streaming_metrics_installed", False):
        return application
    application.state.streaming_metrics_installed = True

    @application.middleware("http")
    async def streaming_metrics(request: Request, call_next):
        if request.method.upper() != "POST" or request.url.path not in _INFERENCE_PATHS:
            return await call_next(request)

        started_at = time.perf_counter()
        response = await call_next(request)

        prepared = getattr(request.state, "prepared_inference_request", None)
        canonical = getattr(prepared, "canonical", None)
        if canonical is None or canonical.stream is not True or response.status_code >= 400:
            return response

        manager = getattr(request.app.state, "runtime_manager", None)
        if manager is None or not hasattr(response, "body_iterator"):
            return response
        try:
            runtime = manager.resolve(canonical.model)
        except (LookupError, RuntimeError):
            return response

        recorder = StreamTimingRecorder(started_at=started_at)
        original_iterator = response.body_iterator

        async def observed_body():
            completed = False
            try:
                async for chunk in original_iterator:
                    recorder.observe(chunk)
                    yield chunk
                completed = True
            finally:
                metrics = recorder.finish(completed=completed)
                if metrics is not None:
                    # This snapshot belongs to this request only. Do not merge in
                    # token counts from a previous request or cumulative runtime state.
                    record_runtime_metrics(runtime, metrics)

        response.body_iterator = observed_body()
        return response

    return application


def _sse_line_has_model_output(line: str) -> bool:
    text = line.strip()
    if not text.startswith("data:"):
        return False
    payload = text[5:].strip()
    if not payload or payload == "[DONE]":
        return False
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return False
    if not isinstance(event, Mapping):
        return False

    choices = event.get("choices")
    if not isinstance(choices, list):
        return False
    for choice in choices:
        if not isinstance(choice, Mapping):
            continue
        delta = choice.get("delta")
        if isinstance(delta, Mapping):
            content = delta.get("content")
            if isinstance(content, str) and content:
                return True
        text_value = choice.get("text")
        if isinstance(text_value, str) and text_value:
            return True
    return False
