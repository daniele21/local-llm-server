from __future__ import annotations

import json

from fastapi.testclient import TestClient

from local_llm_server.core.contracts import GenerationOptions, InferenceRequest, OutputConstraints, TaskType
from local_llm_server.evaluation_service import ResidentRuntimeExecutor
from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def __init__(self, *, completed_content: str, stream_chunks=None):
        self.completed_content = completed_content
        self.stream_chunks = list(stream_chunks or [])

    def complete(self, payload):
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": self.completed_content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"completion_tokens": 4},
        }

    def stream(self, payload):
        yield from self.stream_chunks

    def close(self):
        pass


def _cfg():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": "/demo",
        "backend": "fake",
        "modalities": ["text"],
        "thinking_mode": "switchable",
        "enable_thinking": True,
        "show_thinking": False,
        "force_json": False,
        "default_temperature": 0.0,
        "default_top_p": 1.0,
        "default_top_k": 40,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "max_concurrent_requests": 1,
    }


def _client(engine):
    manager = ProductRuntimeManager(default_model="demo")
    manager.add(_cfg(), engine)
    application = create_app(manager, settings=ServerSettings())
    install_product_http_stack(application)
    return TestClient(application), manager


def _stream_event(content=None, *, finish_reason=None):
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "model": "org/demo",
        "choices": [
            {
                "index": 0,
                "delta": {} if content is None else {"content": content},
                "finish_reason": finish_reason,
            }
        ],
    }


def _aggregate_sse_content(text: str) -> tuple[str, list[dict]]:
    content = []
    payloads = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block.startswith("data:"):
            continue
        raw = block[5:].strip()
        if not raw or raw == "[DONE]":
            continue
        payload = json.loads(raw)
        payloads.append(payload)
        for choice in payload.get("choices") or []:
            delta = choice.get("delta") or {}
            value = delta.get("content")
            if isinstance(value, str):
                content.append(value)
    return "".join(content), payloads


def test_nonstream_structured_response_exposes_only_parseable_final_json():
    client, _manager = _client(_Engine(completed_content='private chain</think>{"answer":42}'))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo",
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
            "show_thinking": False,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    final = payload["choices"][0]["message"]["content"]
    assert json.loads(final) == {"answer": 42}
    assert final == '{"answer":42}'
    assert "private chain" not in final
    assert payload["structured_output"] == {"answer": 42}


def test_structured_response_never_mixes_reasoning_even_when_visibility_requested():
    client, _manager = _client(_Engine(completed_content='<think>private</think>{"answer":42}'))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo",
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
            "show_thinking": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["thinking"] == "private"
    assert json.loads(payload["choices"][0]["message"]["content"]) == {"answer": 42}


def test_nonstream_malformed_final_json_returns_typed_model_output_error():
    client, _manager = _client(_Engine(completed_content='private</think>{"answer":'))

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo",
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "invalid_model_output"


def test_structured_stream_buffers_final_answer_and_emits_one_valid_json_payload():
    engine = _Engine(
        completed_content="unused",
        stream_chunks=[
            _stream_event("<thi"),
            _stream_event("nk>private"),
            _stream_event("</th"),
            _stream_event('ink>{"answer":'),
            _stream_event("42}"),
            _stream_event(None, finish_reason="stop"),
        ],
    )
    client, _manager = _client(engine)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo",
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
            "show_thinking": False,
            "stream": True,
        },
    )

    assert response.status_code == 200
    final, payloads = _aggregate_sse_content(response.text)
    assert final == '{"answer":42}'
    assert json.loads(final) == {"answer": 42}
    assert "private" not in response.text
    assert not any(payload.get("error") for payload in payloads)


def test_structured_stream_malformed_final_json_emits_typed_error_not_repair():
    client, _manager = _client(
        _Engine(
            completed_content="unused",
            stream_chunks=[
                _stream_event('reason</think>{"answer":'),
                _stream_event(None, finish_reason="stop"),
            ],
        )
    )

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "demo",
            "messages": [{"role": "user", "content": "return json"}],
            "response_format": {"type": "json_object"},
            "enable_thinking": True,
            "stream": True,
        },
    )

    _final, payloads = _aggregate_sse_content(response.text)
    errors = [payload["error"] for payload in payloads if payload.get("error")]
    assert len(errors) == 1
    assert errors[0]["code"] == "invalid_model_output"


def test_evaluation_uses_same_final_normalization_before_scoring_contract():
    engine = _Engine(completed_content='private reasoning</think>{"answer":42}')
    manager = ProductRuntimeManager(default_model="demo")
    runtime = manager.add(_cfg(), engine)

    result = ResidentRuntimeExecutor(manager, runtime=runtime).execute(
        InferenceRequest(
            task=TaskType.STRUCTURED_GENERATION,
            model="demo",
            input_text="return json",
            generation=GenerationOptions(temperature=0.0, enable_thinking=True),
            output=OutputConstraints(format="json_object"),
        )
    )

    assert result.content == '{"answer":42}'
    assert result.structured_output == {"answer": 42}
    assert result.metadata["reasoning_separated"] is True
