from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

from local_llm_server.engine import MLXEngine
from local_llm_server.metrics_adapters import metrics_from_completion_response
from local_llm_server.mlx_generation_evidence import openai_evidence_from_mlx_generation


class _Tokenizer:
    def __init__(self):
        self.calls = []

    def apply_chat_template(self, messages, *, add_generation_prompt, **kwargs):
        self.calls.append((messages, add_generation_prompt, kwargs))
        return [1, 2, 3]


def _engine():
    engine = object.__new__(MLXEngine)
    engine.model_ref = "local/mlx-model"
    engine.cfg = {"max_kv_size": 2048}
    engine.model = object()
    engine.tokenizer = _Tokenizer()
    return engine


def _install_fake_mlx(monkeypatch, responses):
    mlx_lm = ModuleType("mlx_lm")
    sample_utils = ModuleType("mlx_lm.sample_utils")
    captured = {}

    def stream_generate(model, tokenizer, **kwargs):
        captured["stream_generate"] = kwargs
        yield from responses

    def make_sampler(**kwargs):
        captured["sampler"] = kwargs
        return "sampler"

    def make_logits_processors(**kwargs):
        captured["logits"] = kwargs
        return ["processor"]

    mlx_lm.stream_generate = stream_generate
    sample_utils.make_sampler = make_sampler
    sample_utils.make_logits_processors = make_logits_processors
    monkeypatch.setitem(sys.modules, "mlx_lm", mlx_lm)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", sample_utils)
    return captured


def _responses():
    return [
        SimpleNamespace(
            text="he",
            prompt_tokens=10,
            generation_tokens=1,
            prompt_tps=100.0,
            generation_tps=20.0,
            finish_reason=None,
        ),
        SimpleNamespace(
            text="llo",
            prompt_tokens=10,
            generation_tokens=2,
            prompt_tps=100.0,
            generation_tps=25.0,
            finish_reason=None,
        ),
        SimpleNamespace(
            text="",
            prompt_tokens=10,
            generation_tokens=2,
            prompt_tps=100.0,
            generation_tps=25.0,
            finish_reason="stop",
        ),
    ]


def test_generation_evidence_maps_only_explicit_valid_fields():
    usage, timings, finish = openai_evidence_from_mlx_generation(
        SimpleNamespace(
            prompt_tokens=40,
            generation_tokens=12,
            prompt_tps=200.0,
            generation_tps=30.0,
            finish_reason="length",
        )
    )

    assert usage == {
        "prompt_tokens": 40,
        "completion_tokens": 12,
        "total_tokens": 52,
    }
    assert timings == {
        "prompt_ms": 200.0,
        "predicted_ms": 400.0,
        "predicted_per_second": 30.0,
    }
    assert finish == "length"

    missing_usage, missing_timings, missing_finish = openai_evidence_from_mlx_generation(
        SimpleNamespace(
            prompt_tokens=-1,
            generation_tokens=True,
            prompt_tps=0,
            generation_tps=None,
            finish_reason="",
        )
    )
    assert missing_usage == {}
    assert missing_timings == {}
    assert missing_finish is None


def test_mlx_stream_emits_cumulative_usage_timings_and_terminal_evidence(monkeypatch):
    captured = _install_fake_mlx(monkeypatch, _responses())
    engine = _engine()

    chunks = list(
        engine.stream(
            {
                "model": "org/public-alias",
                "messages": [{"role": "user", "content": "hello"}],
                "max_tokens": 12,
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 7,
                "min_p": 0.1,
                "repeat_penalty": 1.1,
                "presence_penalty": 0.2,
                "frequency_penalty": 0.3,
                "enable_thinking": True,
            }
        )
    )

    assert [chunk["choices"][0]["delta"].get("content", "") for chunk in chunks] == [
        "he",
        "llo",
        "",
    ]
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    assert chunks[-1]["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 2,
        "total_tokens": 12,
    }
    assert chunks[-1]["timings"] == {
        "prompt_ms": 100.0,
        "predicted_ms": 80.0,
        "predicted_per_second": 25.0,
    }
    assert captured["stream_generate"]["max_tokens"] == 12
    assert captured["stream_generate"]["max_kv_size"] == 2048
    assert captured["sampler"] == {"temp": 0.2, "top_p": 0.9, "min_p": 0.1, "top_k": 7}
    assert captured["logits"] == {
        "repetition_penalty": 1.1,
        "presence_penalty": 0.2,
        "frequency_penalty": 0.3,
    }
    assert engine.tokenizer.calls[0][2] == {"enable_thinking": True, "thinking": True}


def test_mlx_complete_carries_latest_usage_timings_and_finish_reason(monkeypatch):
    _install_fake_mlx(monkeypatch, _responses())
    engine = _engine()

    result = engine.complete(
        {
            "model": "org/public-alias",
            "messages": [{"role": "user", "content": "hello"}],
        }
    )

    assert result["choices"][0]["message"]["content"] == "hello"
    assert result["choices"][0]["finish_reason"] == "stop"
    assert result["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 2,
        "total_tokens": 12,
    }
    assert result["timings"]["predicted_per_second"] == 25.0

    metrics = metrics_from_completion_response(result)
    assert metrics.counts.input_tokens == 10
    assert metrics.counts.output_tokens == 2
    assert metrics.durations.prompt_prefill_ms == 100.0
    assert metrics.durations.decode_ms == 80.0
    assert metrics.throughput.decode_tokens_per_second == 25.0


def test_mlx_stream_does_not_synthesize_metrics_when_upstream_omits_them(monkeypatch):
    _install_fake_mlx(monkeypatch, [SimpleNamespace(text="x")])
    engine = _engine()

    chunks = list(engine.stream({"messages": [{"role": "user", "content": "hi"}]}))

    assert len(chunks) == 1
    assert chunks[0]["choices"][0]["delta"]["content"] == "x"
    assert "usage" not in chunks[0]
    assert "timings" not in chunks[0]


def test_metrics_only_terminal_response_is_not_dropped(monkeypatch):
    _install_fake_mlx(
        monkeypatch,
        [
            SimpleNamespace(
                text="",
                prompt_tokens=4,
                generation_tokens=0,
                prompt_tps=20.0,
                generation_tps=None,
                finish_reason=None,
            )
        ],
    )
    engine = _engine()

    chunks = list(engine.stream({"messages": [{"role": "user", "content": "hi"}]}))

    assert len(chunks) == 1
    assert chunks[0]["choices"] == []
    assert chunks[0]["usage"] == {
        "prompt_tokens": 4,
        "completion_tokens": 0,
        "total_tokens": 4,
    }
    assert chunks[0]["timings"] == {"prompt_ms": 200.0}
