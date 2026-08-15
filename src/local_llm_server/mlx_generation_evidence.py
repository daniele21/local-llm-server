"""Translate explicit MLX generation-response evidence into OpenAI-style fields.

The helper deliberately maps only values that ``mlx_lm.stream_generate``
provides. Missing/invalid counters and rates stay absent rather than becoming
zero or estimates.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def openai_evidence_from_mlx_generation(
    response: Any,
) -> tuple[dict[str, int], dict[str, float], str | None]:
    """Return ``(usage, timings, finish_reason)`` from one MLX response."""
    prompt_tokens = _nonnegative_int(_field(response, "prompt_tokens"))
    generation_tokens = _nonnegative_int(_field(response, "generation_tokens"))
    prompt_tps = _positive_float(_field(response, "prompt_tps"))
    generation_tps = _positive_float(_field(response, "generation_tps"))
    finish_reason = _optional_string(_field(response, "finish_reason"))

    usage: dict[str, int] = {}
    if prompt_tokens is not None:
        usage["prompt_tokens"] = prompt_tokens
    if generation_tokens is not None:
        usage["completion_tokens"] = generation_tokens
    if prompt_tokens is not None and generation_tokens is not None:
        usage["total_tokens"] = prompt_tokens + generation_tokens

    timings: dict[str, float] = {}
    if prompt_tokens is not None and prompt_tps is not None:
        timings["prompt_ms"] = (prompt_tokens / prompt_tps) * 1000.0
    if generation_tokens is not None and generation_tps is not None:
        timings["predicted_ms"] = (generation_tokens / generation_tps) * 1000.0
    if generation_tps is not None:
        timings["predicted_per_second"] = generation_tps

    return usage, timings, finish_reason


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
