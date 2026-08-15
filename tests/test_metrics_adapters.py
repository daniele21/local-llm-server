from __future__ import annotations

from local_llm_server.metrics_adapters import (
    merge_metrics,
    metrics_from_completion_response,
    metrics_from_runtime_status,
)


def test_runtime_chunk_aliases_do_not_become_token_metrics():
    metrics = metrics_from_runtime_status(
        {
            "tokens_generated": 99,
            "tokens_per_second": 33.0,
            "output_chunks": 4,
            "chunks_per_second": 2.0,
        }
    )

    assert metrics.counts.output_tokens is None
    assert metrics.counts.output_chunks == 4
    assert metrics.throughput.decode_tokens_per_second is None
    assert metrics.throughput.output_chunks_per_second == 2.0


def test_missing_runtime_metrics_remain_unavailable():
    metrics = metrics_from_runtime_status({})

    assert metrics.counts.output_chunks is None
    assert metrics.counts.output_tokens is None
    assert metrics.throughput.output_chunks_per_second is None
    assert metrics.sources == {}


def test_invalid_negative_runtime_values_are_ignored():
    metrics = metrics_from_runtime_status(
        {"output_chunks": -1, "chunks_per_second": -5.0}
    )

    assert metrics.counts.output_chunks is None
    assert metrics.throughput.output_chunks_per_second is None


def test_metric_sources_identify_current_runtime_fields():
    metrics = metrics_from_runtime_status(
        {"output_chunks": 3, "chunks_per_second": 1.5}
    )

    assert metrics.sources == {
        "output_chunks": "runtime_status.output_chunks",
        "output_chunks_per_second": "runtime_status.chunks_per_second",
    }


def test_openai_usage_becomes_true_token_counts():
    metrics = metrics_from_completion_response(
        {"usage": {"prompt_tokens": 17, "completion_tokens": 9, "total_tokens": 26}},
        total_ms=250.0,
    )

    assert metrics.counts.input_tokens == 17
    assert metrics.counts.output_tokens == 9
    assert metrics.counts.output_chunks is None
    assert metrics.durations.total_ms == 250.0
    assert metrics.durations.ttft_ms is None
    assert metrics.sources["input_tokens"] == "response.usage.prompt_tokens"
    assert metrics.sources["output_tokens"] == "response.usage.completion_tokens"


def test_llama_timings_supply_prefill_decode_and_token_throughput():
    metrics = metrics_from_completion_response(
        {
            "timings": {
                "prompt_n": 12,
                "prompt_ms": 40.0,
                "predicted_n": 8,
                "predicted_ms": 200.0,
                "predicted_per_second": 40.0,
            }
        }
    )

    assert metrics.counts.input_tokens == 12
    assert metrics.counts.output_tokens == 8
    assert metrics.durations.prompt_prefill_ms == 40.0
    assert metrics.durations.decode_ms == 200.0
    assert metrics.throughput.decode_tokens_per_second == 40.0
    assert metrics.durations.ttft_ms is None


def test_usage_precedes_llama_timing_token_count_when_both_exist():
    metrics = metrics_from_completion_response(
        {
            "usage": {"prompt_tokens": 20, "completion_tokens": 10},
            "timings": {"prompt_n": 99, "predicted_n": 77},
        }
    )

    assert metrics.counts.input_tokens == 20
    assert metrics.counts.output_tokens == 10


def test_merge_metrics_combines_token_and_chunk_evidence_without_aliasing():
    response_metrics = metrics_from_completion_response(
        {"usage": {"prompt_tokens": 5, "completion_tokens": 3}}
    )
    runtime_metrics = metrics_from_runtime_status(
        {"output_chunks": 2, "chunks_per_second": 1.0}
    )

    merged = merge_metrics(response_metrics, runtime_metrics)
    assert merged.counts.input_tokens == 5
    assert merged.counts.output_tokens == 3
    assert merged.counts.output_chunks == 2
    assert merged.throughput.output_chunks_per_second == 1.0
