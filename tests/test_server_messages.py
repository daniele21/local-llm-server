from __future__ import annotations

import json
from unittest.mock import patch

from local_llm_server.server import _normalize_messages


def test_normalize_messages_preserves_multimodal_content():
    messages = _normalize_messages(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_audio", "input_audio": {"data": "abc", "format": "wav"}},
                        {"type": "text", "text": "Trascrivi"},
                    ],
                }
            ]
        }
    )

    assert messages[0]["content"][0]["type"] == "input_audio"


def test_normalize_messages_preserves_image_content():
    messages = _normalize_messages(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
                        {"type": "text", "text": "Descrivi l'immagine."},
                    ],
                }
            ]
        }
    )

    assert isinstance(messages[0]["content"], list)
    assert messages[0]["content"][0]["type"] == "image_url"


def test_normalize_messages_flattens_text_parts():
    messages = _normalize_messages(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "A"},
                        {"type": "text", "text": "B"},
                    ],
                }
            ]
        }
    )

    assert messages == [{"role": "user", "content": "A\nB"}]


def test_chat_completion_request_params():
    from local_llm_server.server import ChatCompletionRequest

    req = ChatCompletionRequest(
        messages=[{"role": "user", "content": "hi"}],
        enable_thinking=True,
        show_thinking=False,
        enable_reasoning=True,
        show_reasoning=False,
    )

    assert req.enable_thinking is True
    assert req.show_thinking is False
    assert req.enable_reasoning is True
    assert req.show_reasoning is False


def test_build_response_hides_thinking_from_exposed_content():
    from local_llm_server.server import _build_response

    response = _build_response(
        {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "<think>private reasoning</think>final answer",
                    },
                }
            ],
            "usage": {"completion_tokens": 2},
        },
        model_id="test-model",
        backend="test-backend",
        started_at=1.0,
        finished_at=2.0,
        show_thinking=False,
    )

    assert response["content"] == "final answer"
    assert response["choices"][0]["message"]["content"] == "final answer"
    assert response["raw_output"] == "<think>private reasoning</think>final answer"
    assert response["thinking"] == "private reasoning"


def test_build_response_can_expose_thinking_when_requested():
    from local_llm_server.server import _build_response

    response = _build_response(
        {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "<think>private reasoning</think>final answer",
                    },
                }
            ],
            "usage": {"completion_tokens": 2},
        },
        model_id="test-model",
        backend="test-backend",
        started_at=1.0,
        finished_at=2.0,
        show_thinking=True,
    )

    assert response["content"] == "<think>private reasoning</think>final answer"
    assert response["choices"][0]["message"]["content"] == "<think>private reasoning</think>final answer"


def test_llama_server_maps_enable_thinking_to_template_kwargs():
    from local_llm_server.engine import LlamaServerEngine

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "ok"}}]}'

    engine = LlamaServerEngine.__new__(LlamaServerEngine)
    engine.base_url = "http://127.0.0.1:8091"
    engine.cfg = {"timeout": 1}

    with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
        engine.complete({
            "messages": [{"role": "user", "content": "hi"}],
            "enable_thinking": True,
        })

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert "enable_thinking" not in payload
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}
