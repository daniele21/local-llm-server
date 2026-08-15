"""Adapters from backend/runtime evidence into the canonical metric schema."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .metrics import (
    CountMetrics,
    DurationMetrics,
    InferenceMetrics,
    ThroughputMetrics,
)


def metrics_from_runtime_status(status: Mapping[str, Any]) -> InferenceMetrics:
    """Map only metrics whose current runtime semantics are trustworthy.

    The historical ``tokens_generated`` and ``tokens_per_second`` fields are
    compatibility aliases backed by output chunk counts, so they are
    deliberately ignored here.
    """
    output_chunks = _nonnegative_int(status.get("output_chunks"))
    chunks_per_second = _nonnegative_float(status.get("chunks_per_second"))

    sources: dict[str, str] = {}
    if output_chunks is not None:
        sources["output_chunks"] = "runtime_status.output_chunks"
    if chunks_per_second is not None:
        sources["output_chunks_per_second"] = "runtime_status.chunks_per_second"

    return InferenceMetrics(
        counts=CountMetrics(
            input_tokens=None,
            output_tokens=None,
            output_chunks=output_chunks,
        ),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=None,
            output_chunks_per_second=chunks_per_second,
        ),
        sources=sources,
    )


def metrics_from_completion_response(
    response: Mapping[str, Any],
    *,
    total_ms: float | None = None,
) -> InferenceMetrics:
    """Normalize trustworthy counters/timings from one completed response.

    OpenAI-compatible ``usage`` token counters are accepted as explicit token
    evidence. llama.cpp-style ``timings`` fields are accepted when present.
    TTFT is intentionally left unavailable because a completed response cannot
    reconstruct time-to-first-token without a streaming timestamp.
    """
    usage = response.get("usage")
    usage_map = usage if isinstance(usage, Mapping) else {}
    timings = response.get("timings")
    timing_map = timings if isinstance(timings, Mapping) else {}

    input_tokens = _nonnegative_int(usage_map.get("prompt_tokens"))
    output_tokens = _nonnegative_int(usage_map.get("completion_tokens"))
    sources: dict[str, str] = {}

    if input_tokens is not None:
        sources["input_tokens"] = "response.usage.prompt_tokens"
    if output_tokens is not None:
        sources["output_tokens"] = "response.usage.completion_tokens"

    # llama.cpp server timing payloads expose prompt/predicted token counts.
    # Use them only as a fallback when the OpenAI usage block is absent.
    if input_tokens is None:
        input_tokens = _nonnegative_int(timing_map.get("prompt_n"))
        if input_tokens is not None:
            sources["input_tokens"] = "response.timings.prompt_n"
    if output_tokens is None:
        output_tokens = _nonnegative_int(timing_map.get("predicted_n"))
        if output_tokens is not None:
            sources["output_tokens"] = "response.timings.predicted_n"

    prompt_ms = _nonnegative_float(timing_map.get("prompt_ms"))
    decode_ms = _nonnegative_float(timing_map.get("predicted_ms"))
    decode_tps = _nonnegative_float(timing_map.get("predicted_per_second"))
    measured_total_ms = _nonnegative_float(total_ms)

    if prompt_ms is not None:
        sources["prompt_prefill_ms"] = "response.timings.prompt_ms"
    if decode_ms is not None:
        sources["decode_ms"] = "response.timings.predicted_ms"
    if decode_tps is not None:
        sources["decode_tokens_per_second"] = "response.timings.predicted_per_second"
    if measured_total_ms is not None:
        sources["total_ms"] = "caller.wall_clock"

    return InferenceMetrics(
        durations=DurationMetrics(
            prompt_prefill_ms=prompt_ms,
            ttft_ms=None,
            decode_ms=decode_ms,
            total_ms=measured_total_ms,
        ),
        counts=CountMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            output_chunks=None,
        ),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=decode_tps,
            output_chunks_per_second=None,
        ),
        sources=sources,
    )


def merge_metrics(*metrics: InferenceMetrics) -> InferenceMetrics:
    """Merge complementary evidence without replacing known values with None."""
    if not metrics:
        return InferenceMetrics()

    def first_value(path: str):
        for item in metrics:
            owner, field = path.split(".", 1)
            value = getattr(getattr(item, owner), field)
            if value is not None:
                return value
        return None

    sources: dict[str, str] = {}
    for item in reversed(metrics):
        sources.update(item.sources)

    return InferenceMetrics(
        durations=DurationMetrics(
            queue_wait_ms=first_value("durations.queue_wait_ms"),
            model_load_ms=first_value("durations.model_load_ms"),
            prompt_prefill_ms=first_value("durations.prompt_prefill_ms"),
            ttft_ms=first_value("durations.ttft_ms"),
            decode_ms=first_value("durations.decode_ms"),
            total_ms=first_value("durations.total_ms"),
        ),
        counts=CountMetrics(
            input_tokens=first_value("counts.input_tokens"),
            output_tokens=first_value("counts.output_tokens"),
            output_chunks=first_value("counts.output_chunks"),
        ),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=first_value("throughput.decode_tokens_per_second"),
            output_chunks_per_second=first_value("throughput.output_chunks_per_second"),
        ),
        load_kind=next((item.load_kind for item in metrics if item.load_kind.value != "unknown"), metrics[0].load_kind),
        cache_kind=next((item.cache_kind for item in metrics if item.cache_kind.value != "unknown"), metrics[0].cache_kind),
        termination_reason=next((item.termination_reason for item in metrics if item.termination_reason is not None), None),
        resource_snapshot_id=next((item.resource_snapshot_id for item in metrics if item.resource_snapshot_id is not None), None),
        sources=sources,
    )


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _nonnegative_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if result >= 0 else None
