"""Adapters from existing runtime status into the canonical metric schema."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .metrics import CountMetrics, InferenceMetrics, ThroughputMetrics


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


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _nonnegative_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if result >= 0 else None
