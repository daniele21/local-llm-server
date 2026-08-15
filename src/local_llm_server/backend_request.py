"""Canonical inference request -> existing engine kwargs translation.

This adapter is the migration owner for backend request construction. It keeps
current engine compatibility defaults while allowing the HTTP middleware and
future worker paths to share one deterministic translation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core.contracts import InferenceRequest


@dataclass(frozen=True, slots=True)
class PreparedBackendRequest:
    kwargs: Mapping[str, Any]
    max_tokens: int | None
    show_thinking: bool
    stream: bool


def build_backend_request(
    canonical: InferenceRequest,
    *,
    runtime_config: Mapping[str, Any],
    runtime_model_id: str,
    show_thinking_override: bool | None = None,
) -> PreparedBackendRequest:
    """Translate canonical chat/generation state to the current engine contract."""
    generation = canonical.generation
    thinking_mode = str(runtime_config.get("thinking_mode", "none"))

    enable_thinking = generation.enable_thinking
    if enable_thinking is None:
        enable_thinking = bool(runtime_config.get("enable_thinking", False))

    show_thinking = (
        bool(show_thinking_override)
        if show_thinking_override is not None
        else bool(runtime_config.get("show_thinking", False))
    )

    kwargs: dict[str, Any] = {
        "messages": [dict(message) for message in canonical.messages],
        "temperature": _resolved_float(
            generation.temperature,
            runtime_config.get("default_temperature"),
            0.0,
        ),
        "top_p": _resolved_float(
            generation.top_p,
            runtime_config.get("default_top_p"),
            1.0,
        ),
        "top_k": _resolved_int(
            generation.top_k,
            runtime_config.get("default_top_k"),
            40,
        ),
        "min_p": _resolved_float(
            generation.min_p,
            runtime_config.get("default_min_p"),
            0.05,
        ),
        "repeat_penalty": _resolved_float(
            generation.repeat_penalty,
            runtime_config.get("default_repeat_penalty"),
            1.1,
        ),
        "presence_penalty": _resolved_float(generation.presence_penalty, None, 0.0),
        "frequency_penalty": _resolved_float(generation.frequency_penalty, None, 0.0),
        "model": runtime_model_id,
    }

    if thinking_mode == "switchable":
        kwargs["enable_thinking"] = bool(enable_thinking)

    if generation.max_tokens is not None:
        kwargs["max_tokens"] = int(generation.max_tokens)
    if generation.seed is not None:
        kwargs["seed"] = int(generation.seed)
    if generation.stop is not None:
        kwargs["stop"] = (
            list(generation.stop)
            if isinstance(generation.stop, tuple)
            else generation.stop
        )

    if canonical.output.format is not None:
        if canonical.output.format == "json_schema" and canonical.output.json_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": dict(canonical.output.json_schema),
            }
        else:
            kwargs["response_format"] = {"type": canonical.output.format}
    elif bool(runtime_config.get("force_json", False)):
        kwargs["response_format"] = {"type": "json_object"}

    return PreparedBackendRequest(
        kwargs=kwargs,
        max_tokens=generation.max_tokens,
        show_thinking=show_thinking,
        stream=canonical.stream,
    )


def resolve_show_thinking_override(payload: Mapping[str, Any]) -> bool | None:
    """Resolve current public aliases without moving them into backend logic."""
    value = payload.get("show_thinking")
    if value is None:
        value = payload.get("show_reasoning")
    return None if value is None else bool(value)


def _resolved_float(primary: Any, configured: Any, fallback: float) -> float:
    value = primary if primary is not None else configured
    return fallback if value is None else float(value)


def _resolved_int(primary: Any, configured: Any, fallback: int) -> int:
    value = primary if primary is not None else configured
    return fallback if value is None else int(value)
