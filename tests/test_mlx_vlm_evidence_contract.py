from __future__ import annotations

import json
from types import SimpleNamespace

from local_llm_server.engine import MLXVLMServerEngine
from local_llm_server.metrics_adapters import metrics_from_completion_response


class _Response:
    def __init__(self, *, body=None, lines=None):
        self.body = body
        self.lines = list(lines or [])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.body or b""

    def __iter__(self):
        return iter(self.lines)


def _engine():
    engine = object.__new__(MLXVLMServerEngine)
    engine.cfg = {
        "timeout": 12,
        "thinking_mode": "switchable",
    }
    engine.model_path = "/private/mlx-vlm/model"
    engine.base_url = "http://127.0.0.1:8092"
    engine.process = None
    return engine


def test_nonstream_vlm_proxy_preserves_usage_and_timings_for_canonical_mapper(monkeypatch):
    response_payload = {
        "id": "chatcmpl-vlm",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "a cat"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 4, "total_tokens": 24},
        "timings": {
            "prompt_ms": 80.0,
            "predicted_ms": 100.0,
            "predicted_per_second": 40.0,
        },
    }
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(body=json.dumps(response_payload).encode("utf-8"))

    monkeypatch.setattr("local_llm_server.engine.urllib.request.urlopen", fake_urlopen)
    engine = _engine()

    raw = engine.complete(
        {
            "model": "public-registry-alias",
            "messages": [{"role": "user", "content": "describe image"}],
            "repeat_penalty": 1.1,
            "enable_thinking": True,
        }
    )
    metrics = metrics_from_completion_response(raw)

    assert raw["timings"]["predicted_per_second"] == 40.0
    assert metrics.counts.input_tokens == 20
    assert metrics.counts.output_tokens == 4
    assert metrics.durations.prompt_prefill_ms == 80.0
    assert metrics.durations.decode_ms == 100.0
    assert metrics.throughput.decode_tokens_per_second == 40.0
    assert metrics.sources["decode_tokens_per_second"] == "response.timings.predicted_per_second"

    assert captured["body"]["model"] == "/private/mlx-vlm/model"
    assert captured["body"]["stream"] is False
    assert captured["body"]["repetition_penalty"] == 1.1
    assert captured["body"]["enable_thinking"] is True
    assert "repeat_penalty" not in captured["body"]
    assert captured["timeout"] == 12.0


def test_stream_vlm_proxy_preserves_terminal_usage_and_timings_event(monkeypatch):
    events = [
        {
            "id": "chatcmpl-vlm",
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": {"content": "cat"}, "finish_reason": None}],
        },
        {
            "id": "chatcmpl-vlm",
            "object": "chat.completion.chunk",
            "choices": [],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
            "timings": {
                "prompt_ms": 60.0,
                "predicted_ms": 75.0,
                "predicted_per_second": 40.0,
            },
        },
    ]
    lines = [
        f"data: {json.dumps(event)}\n\n".encode("utf-8")
        for event in events
    ] + [b"data: [DONE]\n\n"]
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _Response(lines=lines)

    monkeypatch.setattr("local_llm_server.engine.urllib.request.urlopen", fake_urlopen)
    engine = _engine()

    chunks = list(
        engine.stream(
            {
                "model": "alias",
                "messages": [{"role": "user", "content": "look"}],
                "show_thinking": False,
            }
        )
    )

    assert chunks == events
    terminal_metrics = metrics_from_completion_response(chunks[-1])
    assert terminal_metrics.counts.input_tokens == 12
    assert terminal_metrics.counts.output_tokens == 3
    assert terminal_metrics.throughput.decode_tokens_per_second == 40.0
    assert captured["body"]["model"] == "/private/mlx-vlm/model"
    assert captured["body"]["stream"] is True
    assert "show_thinking" not in captured["body"]


def test_vlm_proxy_does_not_synthesize_metrics_when_backend_omits_them(monkeypatch):
    payload = {
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }
        ]
    }

    monkeypatch.setattr(
        "local_llm_server.engine.urllib.request.urlopen",
        lambda request, timeout: _Response(body=json.dumps(payload).encode("utf-8")),
    )
    metrics = metrics_from_completion_response(_engine().complete({"messages": []}))

    assert metrics.counts.input_tokens is None
    assert metrics.counts.output_tokens is None
    assert metrics.durations.prompt_prefill_ms is None
    assert metrics.durations.decode_ms is None
    assert metrics.throughput.decode_tokens_per_second is None
    assert metrics.sources == {}
