from __future__ import annotations

import json
from pathlib import Path

from local_llm_server.device_evidence_diagnostics import campaign_diagnostics


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _evaluation(run_id: str, fingerprint: str) -> dict:
    sample_ids = [f"sample-{index:02d}" for index in range(10)]
    return {
        "manifest": {
            "run_id": run_id,
            "test_set_identity": "d" * 64,
            "sample_ids": sample_ids,
            "model": "demo",
            "runtime_fingerprint": fingerprint,
            "reasoning_profile": {
                "requested": "off",
                "runtime_mode": "switchable",
                "effective": "off",
                "request_override": True,
            },
        },
        "complete": True,
        "results": [
            {
                "sample_id": sample_id,
                "succeeded": True,
                "scores": [{"name": "objective", "value": 1.0, "passed": True}],
                "metrics": {"wall_time_seconds": 0.1},
            }
            for sample_id in sample_ids
        ],
    }


def test_diagnostics_explain_evaluation_and_rrg5_review_causes(tmp_path: Path) -> None:
    _write(
        tmp_path / "campaign-summary.json",
        {
            "phases": {
                "evaluation_ev_3": {"status": "FAIL"},
                "validate_minimum_l2_bundle": {"status": "FAIL"},
                "multimodel_rrg_5": {"status": "FAIL"},
            }
        },
    )
    _write(tmp_path / "evaluation-off-a.json", _evaluation("a", "a" * 64))
    _write(tmp_path / "evaluation-off-b.json", _evaluation("b", "b" * 64))
    _write(
        tmp_path / "l2-device-bundle-summary.json",
        {"errors": ["evaluation repeat: runs are not attribution-safe comparable evidence"]},
    )
    _write(
        tmp_path / "multimodel-review.json",
        {
            "state": "insufficient",
            "reasons": [
                "one_or_more_complete_cycles_lack_transient_overlap",
                "one_or_more_shutdown_under_load_procedures_incomplete",
            ],
        },
    )

    messages = campaign_diagnostics(tmp_path)

    assert "EV-3: runtime fingerprint changed; deltas are descriptive only" in messages
    assert (
        "L2 bundle: evaluation repeat: runs are not attribution-safe comparable evidence"
        in messages
    )
    assert "RRG-5 review state: insufficient" in messages
    assert "RRG-5: one_or_more_complete_cycles_lack_transient_overlap" in messages
    assert "RRG-5: one_or_more_shutdown_under_load_procedures_incomplete" in messages


def test_diagnostics_report_incomplete_evaluation(tmp_path: Path) -> None:
    first = _evaluation("a", "a" * 64)
    second = _evaluation("b", "a" * 64)
    second["complete"] = False
    _write(
        tmp_path / "campaign-summary.json",
        {"phases": {"evaluation_ev_3": {"status": "FAIL"}}},
    )
    _write(tmp_path / "evaluation-off-a.json", first)
    _write(tmp_path / "evaluation-off-b.json", second)

    messages = campaign_diagnostics(tmp_path)

    assert "EV-3: run B is incomplete" in messages
    assert "EV-3: both runs must be complete" in messages


def test_diagnostics_explain_rrg5_cycle_and_shutdown_subfailures(tmp_path: Path) -> None:
    _write(
        tmp_path / "campaign-summary.json",
        {"phases": {"multimodel_rrg_5": {"status": "FAIL"}}},
    )
    _write(
        tmp_path / "multimodel-review.json",
        {
            "state": "insufficient",
            "reasons": ["one_or_more_reports_incomplete"],
        },
    )
    _write(
        tmp_path / "multimodel-a.json",
        {
            "status": "incomplete",
            "complete": False,
            "cycles": [
                {
                    "complete": False,
                    "runtime_identities_verified": True,
                    "concurrent_transient_overlap_observed": False,
                    "responses": [{"http_status": 200}, {"http_status": 503}],
                    "configured_accounting_after_unload": {"reservation_count": 1},
                }
            ],
            "shutdown_under_load": {
                "complete": False,
                "first_shutdown_reported_incomplete": True,
                "active_owner_retained_after_timeout": False,
                "configured_accounting_after_retry": {"reservation_count": 2},
            },
        },
    )
    _write(
        tmp_path / "multimodel-b.json",
        {
            "status": "incomplete",
            "complete": False,
            "cycles": [{"complete": False, "failed_phase": "concurrent_inference", "error_type": "TimeoutError"}],
            "shutdown_under_load": {"complete": False, "failed_phase": "retry_shutdown", "error_type": "RuntimeError"},
        },
    )

    messages = campaign_diagnostics(tmp_path)

    assert "RRG-5 report A: status=incomplete" in messages
    assert "RRG-5 report A cycle 1: concurrent transient accounting overlap was not observed" in messages
    assert "RRG-5 report A cycle 1: inference HTTP statuses=[200, 503]" in messages
    assert "RRG-5 report A cycle 1: accounting was not clean after unload" in messages
    assert "RRG-5 report A shutdown-under-load: active runtime ownership was not retained after timeout" in messages
    assert "RRG-5 report A shutdown-under-load: accounting was not clean after retry" in messages
    assert "RRG-5 report B cycle 1 failed_phase=concurrent_inference error_type=TimeoutError" in messages
    assert "RRG-5 report B shutdown-under-load failed_phase=retry_shutdown error_type=RuntimeError" in messages


def test_diagnostics_use_rrg5_safety_fallback_without_review(tmp_path: Path) -> None:
    _write(
        tmp_path / "campaign-summary.json",
        {
            "phases": {
                "multimodel_rrg_5": {
                    "status": "INCONCLUSIVE",
                    "checks": {"host_safety_refused": True},
                }
            }
        },
    )

    messages = campaign_diagnostics(tmp_path)

    assert messages == ("RRG-5: host-memory safety gate refused execution",)


def test_diagnostics_are_empty_for_green_campaign(tmp_path: Path) -> None:
    _write(
        tmp_path / "campaign-summary.json",
        {
            "phases": {
                "evaluation_ev_3": {"status": "PASS"},
                "validate_minimum_l2_bundle": {"status": "PASS"},
                "multimodel_rrg_5": {"status": "PASS"},
            }
        },
    )

    assert campaign_diagnostics(tmp_path) == ()
