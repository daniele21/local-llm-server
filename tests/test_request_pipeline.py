from __future__ import annotations

import pytest

from local_llm_server.core import ErrorCode, InferenceError, TaskType
from local_llm_server.request_pipeline import prepare_chat_request, public_error_detail


def test_legacy_input_is_canonicalized_before_execution_policy():
    prepared = prepare_chat_request(
        {"input": "hello", "model": "demo"},
        runtime_config={"modalities": ["text"]},
    )

    assert prepared.canonical.task is TaskType.CHAT
    assert prepared.canonical.input_text == "hello"
    assert prepared.messages == ({"role": "user", "content": "hello"},)


def test_remote_http_media_is_rejected_by_default():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/private.png"},
                    },
                    {"type": "text", "text": "describe"},
                ],
            }
        ]
    }

    with pytest.raises(InferenceError) as exc_info:
        prepare_chat_request(payload, runtime_config={"modalities": ["text", "image"]})

    assert exc_info.value.code is ErrorCode.INVALID_REQUEST
    assert exc_info.value.details == {"policy": "remote_media_disabled"}


def test_remote_http_media_requires_explicit_runtime_opt_in():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.png"},
                    }
                ],
            }
        ]
    }

    prepared = prepare_chat_request(
        payload,
        runtime_config={
            "modalities": ["text", "image"],
            "allow_remote_media": True,
        },
    )

    assert prepared.required_modalities == frozenset({"text", "image"})


def test_unsupported_modality_is_typed_before_backend_execution():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_audio", "input_audio": {"data": "abc", "format": "wav"}}
                ],
            }
        ]
    }

    with pytest.raises(InferenceError) as exc_info:
        prepare_chat_request(payload, runtime_config={"modalities": ["text"]})

    assert exc_info.value.code is ErrorCode.UNSUPPORTED_MODALITY
    assert exc_info.value.details["required"] == ["audio", "text"]


def test_public_error_detail_is_bounded_and_structured():
    error = InferenceError(
        ErrorCode.INVALID_REQUEST,
        "invalid",
        details={"policy": "remote_media_disabled"},
    )
    assert public_error_detail(error) == {
        "code": "invalid_request",
        "message": "invalid",
        "retryable": False,
        "details": {"policy": "remote_media_disabled"},
    }
