from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.request_pipeline import prepare_chat_request
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.server import ServerSettings, create_app


class _CaptureEngine:
    backend = "fake"

    def __init__(self):
        self.complete_calls: list[dict] = []
        self.stream_calls: list[dict] = []

    def complete(self, payload):
        self.complete_calls.append(deepcopy(payload))
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        }

    def stream(self, payload):
        self.stream_calls.append(deepcopy(payload))
        yield {
            "id": "chatcmpl-test",
            "object": "chat.completion.chunk",
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": "ok"},
                    "finish_reason": None,
                }
            ],
        }

    def close(self):
        pass


def _cfg():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": "/private/demo",
        "backend": "fake",
        "modalities": ["text"],
        "tasks": ["chat", "structured_generation"],
        "input_modalities": ["text"],
        "output_modalities": ["text"],
        "features": ["streaming", "structured_output", "thinking"],
        "thinking_mode": "switchable",
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
        "default_temperature": 0.0,
        "default_top_p": 0.8,
        "default_top_k": 20,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "max_concurrent_requests": 1,
    }


def _client():
    cfg = _cfg()
    manager = ModelRuntimeManager(default_model="demo")
    engine = _CaptureEngine()
    runtime = manager.add(cfg, engine)
    application = create_app(
        manager,
        settings=ServerSettings(enable_admin_api=False),
    )
    install_product_http_stack(application)
    return TestClient(application), runtime, engine


@pytest.mark.parametrize(
    "payload",
    [
        {
            "model": "demo",
            "messages": [{"role": "user", "content": "hello"}],
        },
        {
            "model": "demo",
            "messages": [
                {"role": "system", "content": "be concise"},
                {"role": "user", "content": "hello"},
            ],
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
            "show_reasoning": True,
        },
        {
            "model": "demo",
            "system_prompt": "Return JSON only",
            "input": "Give me one key",
            "response_format": {"type": "json_object"},
        },
    ],
)
def test_supported_nonstream_route_payload_matches_prepared_backend_request(payload):
    client, runtime, engine = _client()
    expected = prepare_chat_request(
        payload,
        runtime_config=runtime.cfg,
        runtime_model_id=runtime.model_id,
    ).backend

    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200, response.text
    assert len(engine.complete_calls) == 1
    assert engine.complete_calls[0] == dict(expected.kwargs)


def test_supported_stream_route_payload_matches_prepared_backend_request():
    client, runtime, engine = _client()
    payload = {
        "model": "demo",
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.2,
        "max_tokens": 12,
        "enable_thinking": True,
        "show_thinking": False,
        "stream": True,
    }
    expected = prepare_chat_request(
        payload,
        runtime_config=runtime.cfg,
        runtime_model_id=runtime.model_id,
    ).backend

    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200, response.text
    assert "data: [DONE]" in response.text
    assert len(engine.stream_calls) == 1
    assert engine.stream_calls[0] == dict(expected.kwargs)


def test_force_json_configuration_matches_canonical_backend_translation():
    cfg = _cfg()
    cfg["force_json"] = True
    manager = ModelRuntimeManager(default_model="demo")
    engine = _CaptureEngine()
    runtime = manager.add(cfg, engine)
    application = create_app(manager, settings=ServerSettings(enable_admin_api=False))
    install_product_http_stack(application)
    client = TestClient(application)
    payload = {
        "model": "demo",
        "messages": [{"role": "user", "content": "return json"}],
    }
    expected = prepare_chat_request(
        payload,
        runtime_config=runtime.cfg,
        runtime_model_id=runtime.model_id,
    ).backend

    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200, response.text
    assert engine.complete_calls[0] == dict(expected.kwargs)
    assert engine.complete_calls[0]["response_format"] == {"type": "json_object"}
