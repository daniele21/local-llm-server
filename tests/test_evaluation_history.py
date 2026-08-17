from __future__ import annotations

from local_llm_server.evaluation_history import (
    compare_run_summaries,
    summarize_report_payload,
)

_DEFAULT_REASONING = {
    "requested": "off",
    "runtime_mode": "switchable",
    "effective": "off",
    "request_override": False,
}


def _payload(
    run_id: str,
    *,
    model: str = "demo",
    fingerprint: str | None = "a" * 64,
    test_identity: str = "t" * 64,
    samples=("s1", "s2"),
    quality=(1.0, 0.5),
    wall=(1.0, 3.0),
    succeeded=(True, True),
    reasoning_profile=_DEFAULT_REASONING,
):
    results = []
    for index, sample_id in enumerate(samples):
        results.append(
            {
                "sample_id": sample_id,
                "succeeded": succeeded[index],
                "scores": [{"name": "objective", "value": quality[index], "passed": quality[index] == 1.0}],
                "error_code": None,
                "metrics": {
                    "wall_time_seconds": wall[index],
                    "prompt_tokens": 10 + index,
                    "completion_tokens": 2 + index,
                },
            }
        )
    manifest = {
        "run_id": run_id,
        "model": model,
        "test_set_identity": test_identity,
        "sample_ids": list(samples),
        "runtime_fingerprint": fingerprint,
    }
    if reasoning_profile is not None:
        manifest["reasoning_profile"] = dict(reasoning_profile)
    return {
        "manifest": manifest,
        "complete": True,
        "results": results,
    }


def test_summary_aggregates_quality_success_time_tokens_and_reasoning_profile():
    summary = summarize_report_payload(_payload("run-a"))

    assert summary.run_id == "run-a"
    assert summary.sample_count == 2
    assert summary.succeeded_count == 2
    assert summary.scored_count == 2
    assert summary.objective_quality_mean == 0.75
    assert summary.execution_success_rate == 1.0
    assert summary.mean_wall_time_seconds == 2.0
    assert summary.total_input_tokens == 21
    assert summary.total_output_tokens == 5
    assert summary.reasoning_profile == _DEFAULT_REASONING
    assert summary.to_public_dict()["reasoning_profile"] == _DEFAULT_REASONING


def test_same_identity_same_model_and_reasoning_comparison_is_attribution_safe():
    baseline = summarize_report_payload(_payload("base", quality=(0.5, 0.5), wall=(2.0, 2.0)))
    candidate = summarize_report_payload(_payload("candidate", quality=(1.0, 0.5), wall=(1.0, 1.0)))

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is True
    assert comparison.evidence_grade is True
    assert comparison.attribution_safe is True
    assert comparison.reasons == ()
    assert comparison.deltas["objective_quality_mean"] == 0.25
    assert comparison.deltas["mean_wall_time_seconds"] == -1.0


def test_changed_reasoning_profile_is_descriptive_and_blocks_attribution():
    baseline = summarize_report_payload(_payload("base"))
    candidate = summarize_report_payload(
        _payload(
            "candidate",
            reasoning_profile={
                "requested": "on",
                "runtime_mode": "switchable",
                "effective": "on",
                "request_override": True,
            },
        )
    )

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is True
    assert comparison.evidence_grade is True
    assert comparison.attribution_safe is False
    assert any("reasoning profile changed" in reason for reason in comparison.reasons)
    assert comparison.deltas["objective_quality_mean"] == 0.0


def test_legacy_missing_reasoning_profile_remains_readable_but_not_evidence_grade():
    baseline = summarize_report_payload(_payload("legacy", reasoning_profile=None))
    candidate = summarize_report_payload(_payload("candidate"))

    comparison = compare_run_summaries(baseline, candidate)

    assert baseline.reasoning_profile is None
    assert comparison.comparable is True
    assert comparison.evidence_grade is False
    assert comparison.attribution_safe is False
    assert any("reasoning profile missing" in reason for reason in comparison.reasons)


def test_changed_runtime_fingerprint_keeps_descriptive_comparison_but_blocks_attribution():
    baseline = summarize_report_payload(_payload("base", fingerprint="a" * 64))
    candidate = summarize_report_payload(_payload("candidate", fingerprint="b" * 64))

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is True
    assert comparison.evidence_grade is True
    assert comparison.attribution_safe is False
    assert any("descriptive only" in reason for reason in comparison.reasons)
    assert comparison.deltas["objective_quality_mean"] == 0.0


def test_cross_model_comparison_is_descriptive_even_with_fingerprints():
    baseline = summarize_report_payload(_payload("base", model="model-a", fingerprint="a" * 64))
    candidate = summarize_report_payload(_payload("candidate", model="model-b", fingerprint="b" * 64))

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is True
    assert comparison.evidence_grade is True
    assert comparison.attribution_safe is False
    assert any("cross-model" in reason for reason in comparison.reasons)


def test_missing_fingerprint_is_exploratory_comparison():
    baseline = summarize_report_payload(_payload("base", fingerprint=None))
    candidate = summarize_report_payload(_payload("candidate", fingerprint="b" * 64))

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is True
    assert comparison.evidence_grade is False
    assert comparison.attribution_safe is False
    assert any("fingerprint missing" in reason for reason in comparison.reasons)


def test_different_sample_selection_is_not_comparable_and_deltas_are_suppressed():
    baseline = summarize_report_payload(_payload("base", samples=("s1", "s2")))
    candidate = summarize_report_payload(_payload("candidate", samples=("s1", "s3")))

    comparison = compare_run_summaries(baseline, candidate)

    assert comparison.comparable is False
    assert comparison.evidence_grade is False
    assert comparison.attribution_safe is False
    assert comparison.deltas["objective_quality_mean"] is None
    assert any("sample IDs differ" in reason for reason in comparison.reasons)


def test_different_test_set_identity_is_not_comparable():
    baseline = summarize_report_payload(_payload("base", test_identity="a" * 64))
    candidate = summarize_report_payload(_payload("candidate", test_identity="b" * 64))

    comparison = compare_run_summaries(baseline, candidate)
    assert comparison.comparable is False
    assert comparison.deltas["mean_wall_time_seconds"] is None
