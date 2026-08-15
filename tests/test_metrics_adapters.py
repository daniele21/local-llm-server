from __future__ import annotations

from local_llm_server.metrics_adapters import metrics_from_runtime_status


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
