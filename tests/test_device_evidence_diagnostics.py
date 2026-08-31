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
