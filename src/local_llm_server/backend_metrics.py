"""Backend-specific metric adapters that preserve canonical evidence semantics."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .metrics import CountMetrics, DurationMetrics, InferenceMetrics, ThroughputMetrics


def metrics_from_mlx_generation_response(response: Any) -> InferenceMetrics:
    """Map explicit ``mlx_lm.stream_generate`` response fields.

    Current MLX generation responses expose cumulative prompt/generation token
    counts and processing rates. Durations are derived only when both the token
    count and corresponding positive tokens-per-second measurement are present.
    Missing or malformed fields remain unavailable.
    """
    prompt_tokens = _nonnegative_int(_field(response, "prompt_tokens"))
    output_tokens = _nonnegative_int(_field(response, "generation_tokens"))
    prompt_tps = _positive_float(_field(response, "prompt_tps"))
    generation_tps = _positive_float(_field(response, "generation_tps"))
    finish_reason = _optional_string(_field(response, "finish_reason"))

    prompt_ms = (
        (prompt_tokens / prompt_tps) * 1000.0
        if prompt_tokens is not None and prompt_tps is not None
        else None
    )
    decode_ms = (
        (output_tokens / generation_tps) * 1000.0
        if output_tokens is not None and generation_tps is not None
        else None
    )

    sources: dict[str, str] = {}
    if prompt_tokens is not None:
        sources["input_tokens"] = "mlx_generation.prompt_tokens"
    if output_tokens is not None:
        sources["output_tokens"] = "mlx_generation.generation_tokens"
    if prompt_ms is not None:
        sources["prompt_prefill_ms"] = "mlx_generation.prompt_tokens/prompt_tps"
    if decode_ms is not None:
        sources["decode_ms"] = "mlx_generation.generation_tokens/generation_tps"
    if generation_tps is not None:
        sources["decode_tokens_per_second"] = "mlx_generation.generation_tps"
    if finish_reason is not None:
        sources["termination_reason"] = "mlx_generation.finish_reason"

    return InferenceMetrics(
        durations=DurationMetrics(
            prompt_prefill_ms=prompt_ms,
            decode_ms=decode_ms,
        ),
        counts=CountMetrics(
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
        ),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=generation_tps,
        ),
        termination_reason=finish_reason,
        sources=sources,
    )


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _positive_float(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if number > 0 else None


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
