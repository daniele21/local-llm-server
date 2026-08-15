from __future__ import annotations

import pytest

from local_llm_server.metrics import (
    CountMetrics,
    DurationMetrics,
    InferenceMetrics,
    ThroughputMetrics,
)


def test_chunks_are_never_substituted_for_tokens():
    counts = CountMetrics(output_tokens=None, output_chunks=12)
    assert counts.generated_tokens is None
    assert counts.output_chunks == 12


def test_unavailable_metrics_serialize_as_none_not_zero():
    payload = InferenceMetrics().to_public_dict()
    assert payload["durations_ms"]["ttft"] is None
    assert payload["counts"]["output_tokens"] is None
    assert payload["throughput"]["decode_tokens_per_second"] is None


def test_token_and_chunk_throughput_have_distinct_units():
    metrics = InferenceMetrics(
        counts=CountMetrics(output_tokens=20, output_chunks=4),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=10.0,
            output_chunks_per_second=2.0,
        ),
    )
    payload = metrics.to_public_dict()
    assert payload["throughput"]["decode_tokens_per_second"] == 10.0
    assert payload["throughput"]["output_chunks_per_second"] == 2.0


def test_negative_duration_is_invalid():
    with pytest.raises(ValueError):
        DurationMetrics(total_ms=-1)


def test_public_metrics_do_not_have_prompt_or_output_fields():
    payload = InferenceMetrics().to_public_dict()
    assert "prompt" not in payload
    assert "output" not in payload
    assert "messages" not in payload
