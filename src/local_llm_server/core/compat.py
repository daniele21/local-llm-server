"""Compatibility translators from existing public request shapes."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .contracts import (
    GenerationOptions,
    InferenceError,
    InferenceRequest,
    OutputConstraints,
    ErrorCode,
    TaskType,
)


def chat_payload_to_inference_request(payload: Mapping[str, Any]) -> InferenceRequest:
    """Translate current OpenAI/legacy chat payloads into the canonical request.

    This function performs shape translation only. Capability validation,
    scheduling and backend policy intentionally live outside the adapter.
    """
    messages = _normalize_messages(payload)
    modalities = _detect_modalities(messages)
    response_format = payload.get("response_format")

    if "audio" in modalities:
        task = TaskType.TRANSCRIPTION
    elif "image" in modalities:
        task = TaskType.VISION_LANGUAGE
    elif isinstance(response_format, Mapping) and response_format.get("type") in {
        "json_object",
        "json_schema",
    }:
        task = TaskType.STRUCTURED_GENERATION
    else:
        task = TaskType.CHAT

    stop = payload.get("stop")
    if isinstance(stop, list):
        stop = tuple(str(item) for item in stop)
    elif stop is not None:
        stop = str(stop)

    generation = GenerationOptions(
        max_tokens=_optional_int(payload.get("max_tokens") or payload.get("max_output_tokens")),
        temperature=_optional_float(payload.get("temperature")),
        top_p=_optional_float(payload.get("top_p")),
        top_k=_optional_int(payload.get("top_k")),
        min_p=_optional_float(payload.get("min_p")),
        repeat_penalty=_optional_float(payload.get("repeat_penalty")),
        presence_penalty=_optional_float(payload.get("presence_penalty")),
        frequency_penalty=_optional_float(payload.get("frequency_penalty")),
        seed=_optional_int(payload.get("seed")),
        stop=stop,
        enable_thinking=_optional_bool(
            payload.get("enable_thinking")
            if payload.get("enable_thinking") is not None
            else payload.get("enable_reasoning")
        ),
    )

    output = OutputConstraints()
    if isinstance(response_format, Mapping):
        output = OutputConstraints(
            format=str(response_format.get("type") or "") or None,
            json_schema=(
                response_format.get("json_schema")
                if isinstance(response_format.get("json_schema"), Mapping)
                else None
            ),
        )

    return InferenceRequest(
        task=task,
        model=str(payload["model"]) if payload.get("model") is not None else None,
        messages=tuple(messages),
        input_text=_last_user_text(messages),
        generation=generation,
        output=output,
        stream=bool(payload.get("stream", False)),
    )


def _normalize_messages(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_messages = payload.get("messages")
    if isinstance(raw_messages, list):
        messages: list[dict[str, Any]] = []
        for item in raw_messages:
            if not isinstance(item, Mapping):
                continue
            role = str(item.get("role") or "").strip()
            content = item.get("content")
            if isinstance(content, str):
                content = content.strip()
            elif isinstance(content, list):
                content = [dict(part) if isinstance(part, Mapping) else part for part in content]
            if role and content:
                messages.append({"role": role, "content": content})
        if messages:
            return messages

    system_prompt = str(payload.get("system_prompt") or "").strip()
    user_input = str(
        payload.get("input") or payload.get("text") or payload.get("prompt") or ""
    ).strip()
    if not user_input:
        raise InferenceError(
            ErrorCode.INVALID_REQUEST,
            "Missing required field: 'messages' or 'input'.",
        )

    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_input})
    return messages


def _detect_modalities(messages: list[dict[str, Any]]) -> set[str]:
    modalities = {"text"}
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, Mapping):
                continue
            part_type = str(part.get("type") or "")
            if part_type in {"image", "image_url", "input_image"}:
                modalities.add("image")
            elif part_type in {"audio", "input_audio"}:
                modalities.add("audio")
    return modalities


def _last_user_text(messages: list[dict[str, Any]]) -> str | None:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                str(part.get("text"))
                for part in content
                if isinstance(part, Mapping) and part.get("type") == "text" and part.get("text")
            ]
            if text_parts:
                return "\n".join(text_parts)
    return None


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_bool(value: Any) -> bool | None:
    return None if value is None else bool(value)
