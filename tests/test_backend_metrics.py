from __future__ import annotations

from types import SimpleNamespace

from local_llm_server.backend_metrics import metrics_from_mlx_generation_response


def test_mlx_generation_response_maps_only_explicit_cumulative_evidence():
    response = SimpleNamespace(
        prompt_tokens=40,
        prompt_tps=200.0,
        generation_tokens=12,
        generation_tps=30.0,
        finish_reason="stop",
        peak_memory=4.2,
    )

    metrics = metrics_from_mlx_generation_response(response)

    assert metrics.counts.input_tokens == 40
    assert metrics.counts.output_tokens == 12
    assert metrics.durations.prompt_prefill_ms == 200.0
    assert metrics.durations.decode_ms == 400.0
    assert metrics.throughput.decode_tokens_per_second == 30.0
    assert metrics.termination_reason == "stop"
    assert metrics.sources["input_tokens"] == "mlx_generation.prompt_tokens"
    assert metrics.sources["decode_tokens_per_second"] == "mlx_generation.generation_tps"
    assert "peak_memory" not in metrics.sources


def test_mlx_generation_response_accepts_mapping_shape():
    metrics = metrics_from_mlx_generation_response(
        {
            "prompt_tokens": 5,
            "prompt_tps": 10.0,
            "generation_tokens": 2,
            "generation_tps": 4.0,
            "finish_reason": "length",
        }
    )

    assert metrics.durations.prompt_prefill_ms == 500.0
    assert metrics.durations.decode_ms == 500.0
    assert metrics.termination_reason == "length"


def test_mlx_generation_response_preserves_unavailable_for_invalid_fields():
    metrics = metrics_from_mlx_generation_response(
        SimpleNamespace(
            prompt_tokens=-1,
            prompt_tps=0,
            generation_tokens=True,
            generation_tps=None,
            finish_reason=None,
        )
    )

    assert metrics.counts.input_tokens is None
    assert metrics.counts.output_tokens is None
    assert metrics.durations.prompt_prefill_ms is None
    assert metrics.durations.decode_ms is None
    assert metrics.throughput.decode_tokens_per_second is None
    assert metrics.termination_reason is None
    assert metrics.sources == {}
