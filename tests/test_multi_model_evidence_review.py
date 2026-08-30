from __future__ import annotations

from copy import deepcopy

from local_llm_server.multi_model_evidence_review import (
    MultiModelReviewSettings,
    MultiModelReviewState,
    review_multi_model_evidence,
)


def _identity(char: str):
    return {"fingerprint": char * 64, "captured_at": 1.0, "identity": {}}


def _zero_accounting():
    return {
        "resident_committed_bytes": 0,
        "resident_reserved_bytes": 0,
        "transient_committed_bytes": 0,
        "transient_reserved_bytes": 0,
        "reservation_count": 0,
    }


def _report(*, rss_delta: int = 100, available_delta: int = -50, total_memory: int = 16_000):
    cycle = {
        "complete": True,
        "responses": [
            {"model": "a", "http_status": 200, "global_wait_ms": 0.0},
            {"model": "b", "http_status": 200, "global_wait_ms": 0.0},
        ],
        "runtime_identities_verified": True,
        "concurrent_transient_overlap_observed": True,
        "configured_accounting_peak": {
            "resident_committed_bytes": 900,
            "resident_reserved_bytes": 0,
            "transient_committed_bytes": 200,
            "transient_reserved_bytes": 0,
            "reservation_count": 4,
        },
        "configured_accounting_after_unload": _zero_accounting(),
        "post_stop_observation": {
            "rss_after_minus_before_bytes": rss_delta,
            "available_after_minus_before_bytes": available_delta,
        },
        "runtime_identities": [_identity("a"), _identity("b")],
        "automatic_eviction_exercised": False,
    }
    return {
        "schema_version": 1,
        "procedure": {
            "name": "multi_model_resource_governor_v1",
            "cycles": 2,
            "max_tokens": 8,
            "request_estimate_bytes": 100,
            "global_max_running": 2,
            "global_queue_capacity": 4,
            "settle_after_unload_seconds": 2.0,
            "shutdown_timeout_seconds": 0.05,
            "sample_interval_seconds": 0.05,
            "prompt_recorded": False,
            "output_recorded": False,
            "process_ids_recorded": False,
            "automatic_eviction_enabled": False,
        },
        "models": [
            {
                "key": "a",
                "model_id": "org/a",
                "backend": "llama_server",
                "artifact_sha256": "c" * 64,
                "estimate_bytes": 400,
            },
            {
                "key": "b",
                "model_id": "org/b",
                "backend": "llama_server",
                "artifact_sha256": "d" * 64,
                "estimate_bytes": 500,
            },
        ],
        "budget": {
            "resident_estimate_bytes": 900,
            "transient_capacity_bytes": 200,
            "success_margin_bytes": 100,
            "headroom_bytes": 100,
            "host_safety_bytes": 100,
            "usable_budget_bytes": 1_200,
        },
        "host_before": {
            "platform": "darwin",
            "total_memory_bytes": {
                "value": total_memory,
                "source": "measured",
                "unit": "bytes",
            },
        },
        "cycles": [deepcopy(cycle), deepcopy(cycle)],
        "shutdown_under_load": {
            "complete": True,
            "first_shutdown_reported_incomplete": True,
            "active_owner_retained_after_timeout": True,
            "remaining_after_first_shutdown": [
                {"key": "a", "state": "failed", "active_requests": 1}
            ],
            "configured_accounting_after_first_shutdown": {
                "resident_committed_bytes": 400,
                "resident_reserved_bytes": 0,
                "transient_committed_bytes": 0,
                "transient_reserved_bytes": 0,
                "reservation_count": 1,
            },
            "configured_accounting_after_retry": _zero_accounting(),
            "automatic_eviction_exercised": False,
        },
        "status": "complete",
        "complete": True,
        "automatic_eviction_exercised": False,
    }


def test_two_compatible_complete_reports_form_sufficient_observation_set():
    review = review_multi_model_evidence([_report(), _report(rss_delta=-20)])

    assert review.state is MultiModelReviewState.SUFFICIENT_OBSERVATION_SET
    assert review.report_count == 2
    assert review.complete_cycles == 4
    assert review.identity_verified_cycles == 4
    assert review.transient_overlap_cycles == 4
    assert review.clean_accounting_cycles == 4
    assert review.shutdown_complete_reports == 2
    assert review.rss_after_minus_before_bytes == (100, 100, -20, -20)
    public = review.to_public_dict()
    assert public["automatic_eviction_recommendation"] == "not_provided"
    assert public["reclamation_safety_claim"] is False


def test_incompatible_runtime_identity_is_rejected():
    first = _report()
    second = _report()
    second["cycles"][0]["runtime_identities"][0]["fingerprint"] = "e" * 64
    second["cycles"][1]["runtime_identities"][0]["fingerprint"] = "e" * 64

    review = review_multi_model_evidence([first, second])

    assert review.state is MultiModelReviewState.INCOMPATIBLE
    assert "model_runtime_hardware_or_procedure_identity_differs" in review.reasons


def test_different_unified_memory_tier_is_incompatible():
    review = review_multi_model_evidence([_report(total_memory=16_000), _report(total_memory=32_000)])

    assert review.state is MultiModelReviewState.INCOMPATIBLE
    assert "model_runtime_hardware_or_procedure_identity_differs" in review.reasons


def test_identity_flag_without_fingerprint_never_becomes_sufficient():
    first = _report()
    second = _report()
    for cycle in second["cycles"]:
        cycle["runtime_identities"] = [None, None]
        cycle["runtime_identities_verified"] = True

    review = review_multi_model_evidence([first, second])

    assert review.state is MultiModelReviewState.INSUFFICIENT
    assert review.complete_cycles < 4


def test_overlap_flag_without_configured_peak_never_becomes_sufficient():
    first = _report()
    second = _report()
    for cycle in second["cycles"]:
        cycle["configured_accounting_peak"]["transient_committed_bytes"] = 100
        cycle["concurrent_transient_overlap_observed"] = True

    review = review_multi_model_evidence([first, second])

    assert review.state is MultiModelReviewState.INSUFFICIENT
    assert review.complete_cycles < 4


def test_incomplete_or_auto_eviction_report_never_becomes_sufficient():
    first = _report()
    second = _report()
    second["complete"] = False
    second["automatic_eviction_exercised"] = True

    review = review_multi_model_evidence([first, second])

    assert review.state is MultiModelReviewState.INSUFFICIENT
    assert "one_or_more_reports_incomplete" in review.reasons
    assert "automatic_eviction_must_not_be_exercised_in_rrg5" in review.reasons


def test_shutdown_flag_without_retained_failed_owner_never_becomes_sufficient():
    first = _report()
    second = _report()
    second["shutdown_under_load"]["remaining_after_first_shutdown"] = []

    review = review_multi_model_evidence([first, second])

    assert review.state is MultiModelReviewState.INSUFFICIENT
    assert "one_or_more_shutdown_under_load_procedures_incomplete" in review.reasons


def test_minimum_repetition_cannot_be_weakened_below_two_reports():
    try:
        MultiModelReviewSettings(min_reports=1)
    except ValueError as exc:
        assert "min_reports" in str(exc)
    else:
        raise AssertionError("expected reviewer to reject one-report acceptance")
