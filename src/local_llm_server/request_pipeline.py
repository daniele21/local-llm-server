"""Canonical request preparation before backend execution.

This module isolates API-shape translation, privacy/capability policy and the
current engine-kwargs translation from the large FastAPI route implementation.
The route can therefore migrate to one prepared request without changing the
public request contract in the same step.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .backend_request import (
    PreparedBackendRequest,
    build_backend_request,
    resolve_show_thinking_override,
)
from .core import ErrorCode, InferenceError, InferenceRequest, chat_payload_to_inference_request
from .media_policy import RemoteMediaPolicyError, validate_media_sources


@dataclass(frozen=True, slots=True)
class PreparedInferenceRequest:
    canonical: InferenceRequest
    messages: tuple[Mapping[str, Any], ...]
    required_modalities: frozenset[str]
    backend: PreparedBackendRequest


def prepare_chat_request(
    payload: Mapping[str, Any],
    *,
    runtime_config: Mapping[str, Any],
    runtime_model_id: str | None = None,
) -> PreparedInferenceRequest:
    """Translate and validate one existing chat-completions payload.

    API-shape translation and media/modality policy are performed first. The
    resulting canonical request is then translated exactly once into the engine
    kwargs contract that the historical route still expects.
    """
    canonical = chat_payload_to_inference_request(payload)
    messages = tuple(canonical.messages)

    try:
        validate_media_sources(
            messages,
            allow_remote_media=bool(runtime_config.get("allow_remote_media", False)),
        )
    except RemoteMediaPolicyError as exc:
        raise InferenceError(
            ErrorCode.INVALID_REQUEST,
            str(exc),
            retryable=False,
            details={"policy": "remote_media_disabled"},
        ) from exc

    required_modalities = _detect_modalities(messages)
    supported_modalities = frozenset(
        str(item) for item in (runtime_config.get("modalities") or ["text"])
    )
    if not required_modalities.issubset(supported_modalities):
        raise InferenceError(
            ErrorCode.UNSUPPORTED_MODALITY,
            "The selected runtime does not support all request modalities.",
            retryable=False,
            details={
                "required": sorted(required_modalities),
                "supported": sorted(supported_modalities),
            },
        )

    model_id = str(
        runtime_model_id
        or runtime_config.get("model_id")
        or runtime_config.get("model")
        or canonical.model
        or "local"
    )
    backend = build_backend_request(
        canonical,
        runtime_config=runtime_config,
        runtime_model_id=model_id,
        show_thinking_override=resolve_show_thinking_override(payload),
    )

    return PreparedInferenceRequest(
        canonical=canonical,
        messages=messages,
        required_modalities=required_modalities,
        backend=backend,
    )


def public_error_detail(error: InferenceError) -> dict[str, Any]:
    """Return a bounded public representation without backend exception text."""
    return {
        "code": error.code.value,
        "message": error.message,
        "retryable": error.retryable,
        "details": dict(error.details),
    }


def _detect_modalities(messages: tuple[Mapping[str, Any], ...]) -> frozenset[str]:
    required = {"text"}
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, Mapping):
                continue
            part_type = str(part.get("type") or "")
            if part_type in {"image", "image_url", "input_image"}:
                required.add("image")
            elif part_type in {"audio", "input_audio"}:
                required.add("audio")
    return frozenset(required)
