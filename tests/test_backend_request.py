from __future__ import annotations

import pytest

from local_llm_server.backend_request import build_backend_request
from local_llm_server.core import ErrorCode, InferenceError, chat_payload_to_inference_request


def _cfg():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "backend": "llama_server",
        "modalities": ["text"],
        "default_temperature": 0.0,
        "default_top_p": 0.8,
        "default_top_k": 20,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "force_json": False,
        "thinking_mode": "switchable",
        "enable_thinking": False,
        "show_thinking": False,
    }


def test_backend_request_preserves_current_defaults_and_model_identity():
    canonical = chat_payload_to_inference_request(
        {"model": "demo", "messages": [{"role": "user", "content": "hello"}]}
    )

    prepared = build_backend_request(
        canonical,
        runtime_config=_cfg(),
        runtime_model_id="org/demo",
    )

    assert prepared.kwargs == {
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.0,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "repeat_penalty": 1.0,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "model": "org/demo",
        "enable_thinking": False,
    }
    assert prepared.stream is False
    assert prepared.max_tokens is None
    assert prepared.show_thinking is False


def test_backend_request_preserves_generation_overrides_and_alias_shapes():
    canonical = chat_payload_to_inference_request(
        {
            "model": "demo",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.4,
            "top_p": 0.9,
            "top_k": 7,
            "min_p": 0.1,
            "repeat_penalty": 1.2,
            "presence_penalty": 0.3,
            "frequency_penalty": 0.2,
            "max_output_tokens": 64,
            "seed": 42,
            "stop": ["A", "B"],
            "enable_reasoning": True,
            "stream": True,
        }
    )

    prepared = build_backend_request(
        canonical,
        runtime_config=_cfg(),
        runtime_model_id="org/demo",
        show_thinking_override=True,
    )

    assert prepared.kwargs["temperature"] == 0.4
    assert prepared.kwargs["top_p"] == 0.9
    assert prepared.kwargs["top_k"] == 7
    assert prepared.kwargs["min_p"] == 0.1
    assert prepared.kwargs["repeat_penalty"] == 1.2
    assert prepared.kwargs["presence_penalty"] == 0.3
    assert prepared.kwargs["frequency_penalty"] == 0.2
    assert prepared.kwargs["max_tokens"] == 64
    assert prepared.kwargs["seed"] == 42
    assert prepared.kwargs["stop"] == ["A", "B"]
    assert prepared.kwargs["enable_thinking"] is True
    assert prepared.stream is True
    assert prepared.show_thinking is True


def test_structured_output_and_force_json_map_without_client_scoring_logic():
    canonical = chat_payload_to_inference_request(
        {
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
        }
    )
    explicit = build_backend_request(
        canonical,
        runtime_config=_cfg(),
        runtime_model_id="org/demo",
    )
    assert explicit.kwargs["response_format"] == {"type": "json_object"}

    cfg = _cfg()
    cfg["force_json"] = True
    normal = chat_payload_to_inference_request(
        {"messages": [{"role": "user", "content": "return json"}]}
    )
    forced = build_backend_request(
        normal,
        runtime_config=cfg,
        runtime_model_id="org/demo",
    )
    assert forced.kwargs["response_format"] == {"type": "json_object"}


def test_none_thinking_mode_rejects_enable_request():
    cfg = _cfg()
    cfg["thinking_mode"] = "none"
    canonical = chat_payload_to_inference_request(
        {
            "messages": [{"role": "user", "content": "hello"}],
            "enable_thinking": True,
        }
    )

    with pytest.raises(InferenceError) as exc_info:
        build_backend_request(
            canonical,
            runtime_config=cfg,
            runtime_model_id="org/demo",
        )

    assert exc_info.value.code is ErrorCode.INVALID_REQUEST
    assert exc_info.value.details["thinking_mode"] == "none"


def test_always_thinking_mode_rejects_disable_request():
    cfg = _cfg()
    cfg["thinking_mode"] = "always"
    canonical = chat_payload_to_inference_request(
        {
            "messages": [{"role": "user", "content": "hello"}],
            "enable_thinking": False,
        }
    )

    with pytest.raises(InferenceError) as exc_info:
        build_backend_request(
            canonical,
            runtime_config=cfg,
            runtime_model_id="org/demo",
        )

    assert exc_info.value.code is ErrorCode.INVALID_REQUEST
    assert exc_info.value.details["thinking_mode"] == "always"


def test_llama_cpp_switchable_declaration_is_fixed_and_never_forwards_fake_toggle():
    cfg = _cfg()
    cfg["backend"] = "llama_cpp"
    cfg["enable_thinking"] = True
    canonical = chat_payload_to_inference_request(
        {"messages": [{"role": "user", "content": "hello"}]}
    )

    prepared = build_backend_request(
        canonical,
        runtime_config=cfg,
        runtime_model_id="org/demo",
    )

    assert "enable_thinking" not in prepared.kwargs

    disable = chat_payload_to_inference_request(
        {
            "messages": [{"role": "user", "content": "hello"}],
            "enable_reasoning": False,
        }
    )
    with pytest.raises(InferenceError) as exc_info:
        build_backend_request(
            disable,
            runtime_config=cfg,
            runtime_model_id="org/demo",
        )
    assert exc_info.value.details["thinking_mode"] == "always"
