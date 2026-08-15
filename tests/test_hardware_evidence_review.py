from __future__ import annotations

from copy import deepcopy

import pytest

from local_llm_server.hardware_evidence_review import (
    EvidenceReviewSettings,
    EvidenceReviewState,
    review_hardware_evidence,
)


def _report(
    *,
    recovery: int = 3,
    no_recovery: int = 0,
    inconclusive: int = 0,
    errors: int = 0,
    complete: int = 3,
    identity_grade: str = "verified",
):
    cycles = recovery + no_recovery + inconclusive
    return {
        "schema_version": 1,
        "procedure": {
            "name": "worker_reclamation_v1",
            "cycles": cycles,
            "max_tokens": 32,
            "settle_after_stop_seconds": 2.0,
            "prompt_recorded": False,
            "output_recorded": False,
        },
        "report": {
            "descriptor": {
                "procedure": "worker_reclamation_v1",
                "execution_isolation": "subprocess_worker",
                "model_id": "org/demo",
                "backend": "mlx",
                "backend_version": "0.31.7",
                "artifact_sha256": "a" * 64,
                "config_digest": "b" * 64,
                "hardware": {
                    "system": "Darwin",
                    "machine": "arm64",
                    "total_memory_bytes": 16 * 1024**3,
                    "accelerator": "apple-gpu",
                },
                "identity_grade": identity_grade,
            },
            "experiment": {
                "cycle_count": cycles,
                "complete_windows": complete,
                "error_cycles": errors,
                "observations": {
                    "recovery_observed": recovery,
                    "no_recovery_observed": no_recovery,
                    "inconclusive": inconclusive,
                },
                "cycles": [],
                "interpretation": "Observational evidence only.",
            },
        },
    }


def test_repeated_compatible_reports_can_describe_consistent_recovery_without_safety_claim():
    review = review_hardware_evidence([_report(), _report()])

    assert review.state is EvidenceReviewState.CONSISTENT_RECOVERY_OBSERVED
    assert review.report_count == 2
    assert review.complete_windows == 6
    assert review.recovery_observed == 6
    public = review.to_public_dict()
    assert public["automatic_eviction_recommendation"] == "not_provided"
    assert public["production_safety_claim"] is False
    assert "authorize automatic eviction" in public["interpretation"]


def test_repeated_consistent_no_recovery_is_descriptive_not_pass_fail():
    review = review_hardware_evidence(
        [_report(recovery=0, no_recovery=3), _report(recovery=0, no_recovery=3)]
    )

    assert review.state is EvidenceReviewState.CONSISTENT_NO_RECOVERY_OBSERVED
    assert review.no_recovery_observed == 6
    assert review.reasons == ("all_conclusive_cycles_observed_no_recovery",)


def test_mixed_conclusive_results_remain_mixed():
    review = review_hardware_evidence(
        [_report(recovery=2, no_recovery=1), _report(recovery=1, no_recovery=2)]
    )

    assert review.state is EvidenceReviewState.MIXED
    assert review.recovery_observed == 3
    assert review.no_recovery_observed == 3
    assert "not_consistent" in review.reasons[0]


def test_inconclusive_or_error_cycles_block_consistency_state():
    inconclusive = review_hardware_evidence(
        [
            _report(recovery=2, inconclusive=1, complete=3),
            _report(recovery=3, complete=3),
        ]
    )
    errors = review_hardware_evidence(
        [_report(errors=1), _report()]
    )

    assert inconclusive.state is EvidenceReviewState.INSUFFICIENT
    assert "inconclusive_cycles_present" in inconclusive.reasons
    assert errors.state is EvidenceReviewState.INSUFFICIENT
    assert "lifecycle_errors_present" in errors.reasons


def test_verified_identity_and_minimum_repetition_are_required_by_default():
    exploratory = review_hardware_evidence(
        [_report(identity_grade="exploratory"), _report(identity_grade="exploratory")]
    )
    one_report = review_hardware_evidence([_report()])

    assert exploratory.state is EvidenceReviewState.INSUFFICIENT
    assert "verified_identity_required" in exploratory.reasons
    assert one_report.state is EvidenceReviewState.INSUFFICIENT
    assert "insufficient_repeated_reports" in one_report.reasons
    assert "insufficient_complete_cycles" in one_report.reasons


def test_runtime_hardware_or_procedure_mismatch_is_not_aggregated():
    first = _report()
    second = deepcopy(first)
    second["report"]["descriptor"]["config_digest"] = "c" * 64

    review = review_hardware_evidence([first, second])

    assert review.state is EvidenceReviewState.INCOMPATIBLE
    assert review.compatible_report_count == 1
    assert "runtime_hardware_or_procedure_identity_differs" in review.reasons


def test_invalid_schema_is_insufficient_and_never_silently_ignored():
    valid = _report()
    invalid = {"schema_version": 99}

    review = review_hardware_evidence([valid, invalid])

    assert review.state is EvidenceReviewState.INSUFFICIENT
    assert review.report_count == 2
    assert review.compatible_report_count == 1
    assert "one_or_more_reports_have_invalid_schema" in review.reasons


def test_thresholds_are_configurable_without_adding_policy_recommendation():
    review = review_hardware_evidence(
        [_report(recovery=1, complete=1)],
        settings=EvidenceReviewSettings(
            min_reports=1,
            min_complete_cycles=1,
            require_verified_identity=False,
            require_zero_error_cycles=True,
        ),
    )

    assert review.state is EvidenceReviewState.CONSISTENT_RECOVERY_OBSERVED
    assert review.to_public_dict()["automatic_eviction_recommendation"] == "not_provided"


def test_settings_reject_non_positive_thresholds():
    with pytest.raises(ValueError):
        EvidenceReviewSettings(min_reports=0)
    with pytest.raises(ValueError):
        EvidenceReviewSettings(min_complete_cycles=0)
