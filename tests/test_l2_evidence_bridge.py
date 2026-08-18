from __future__ import annotations

import json
from pathlib import Path

from local_llm_server.l2_evidence_bridge import (
    capture_thinking_campaign,
    validate_hardware_bundle,
    validate_product_ui_evidence,
)


def _identity() -> dict:
    return {
        "protocol_version": "local-llm-identity-v1",
        "models": {
            "demo": {
                "model": {
                    "id": "org/demo",
                    "artifact_digest": "sha256:" + "a" * 64,
                    "verification": "verified",
                },
                "runtime": {
                    "name": "llama_cpp",
                    "version": "1.2.3",
                    "config_digest": "b" * 64,
                    "fingerprint": "c" * 64,
                    "evidence_grade": "verified",
                },
            }
        },
    }


def test_thinking_capture_retains_policy_and_drops_prompt_output(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict] = []

    def fake_request(url, *, method="GET", payload=None, timeout=300.0):
        if url.endswith("/v1/runtime/identity"):
            return 200, _identity()
        calls.append(dict(payload or {}))
        if payload["enable_thinking"] is False:
            return 200, {
                "content": "final off",
                "choices": [{"message": {"content": "final off"}}],
                "raw_output": "private raw off",
            }
        return 200, {
            "content": "final on",
            "choices": [{"message": {"content": "final on"}}],
            "thinking": "private chain",
            "raw_output": "private raw on",
        }

    monkeypatch.setattr("local_llm_server.l2_evidence_bridge._request_json", fake_request)
    output = tmp_path / "thinking.json"
    report = capture_thinking_campaign(
        base_url="http://127.0.0.1:8000",
        model="demo",
        output=output,
    )

    assert report["complete"] is True
    assert calls[0]["enable_thinking"] is False
    assert calls[1]["enable_thinking"] is True
    assert calls[0]["show_thinking"] is False
    assert calls[1]["show_thinking"] is False
    serialized = output.read_text(encoding="utf-8")
    assert "local inference can improve privacy" not in serialized
    assert "final off" not in serialized
    assert "final on" not in serialized
    assert "private chain" not in serialized
    assert "private raw" not in serialized
    assert report["on_hidden"]["thinking_metadata_present"] is True
    assert report["on_hidden"]["normal_content_contains_thinking_boundary"] is False


def _evaluation(run_id: str) -> dict:
    sample_ids = [f"sample-{index:02d}" for index in range(10)]
    return {
        "manifest": {
            "run_id": run_id,
            "test_set_id": "general-purpose",
            "test_set_version": "1.0.0",
            "test_set_identity": "d" * 64,
            "sample_ids": sample_ids,
            "model": "demo",
            "seed": 0,
            "runtime_fingerprint": "c" * 64,
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
                "error_code": None,
                "metrics": {
                    "wall_time_seconds": 0.1,
                    "prompt_tokens": 4,
                    "completion_tokens": 2,
                },
            }
            for sample_id in sample_ids
        ],
    }


def _reclamation_report() -> dict:
    return {
        "schema_version": 1,
        "procedure": {
            "name": "worker_reclamation_v1",
            "cycles": 3,
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
                "backend": "llama_cpp",
                "backend_version": "1.2.3",
                "artifact_sha256": "a" * 64,
                "config_digest": "b" * 64,
                "hardware": {
                    "system": "Darwin",
                    "machine": "arm64",
                    "total_memory_bytes": 16 * 1024**3,
                    "accelerator": "apple-gpu",
                },
                "identity_grade": "verified",
            },
            "experiment": {
                "cycle_count": 3,
                "complete_windows": 3,
                "error_cycles": 0,
                "observations": {
                    "recovery_observed": 3,
                    "no_recovery_observed": 0,
                    "inconclusive": 0,
                },
                "cycles": [],
                "interpretation": "Observational evidence only.",
            },
        },
    }


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_hardware_bundle_validates_all_four_real_evidence_gates(tmp_path: Path) -> None:
    thinking = {
        "schema_version": 1,
        "complete": True,
        "requests": {
            "off": {"enable_thinking": False, "show_thinking": False},
            "on_hidden": {"enable_thinking": True, "show_thinking": False},
        },
    }
    _write(tmp_path / "thinking-campaign.json", thinking)
    _write(tmp_path / "evaluation-off-a.json", _evaluation("run-a"))
    _write(tmp_path / "evaluation-off-b.json", _evaluation("run-b"))
    report_a = _reclamation_report()
    report_b = _reclamation_report()
    _write(tmp_path / "reclamation-a.json", report_a)
    _write(tmp_path / "reclamation-b.json", report_b)

    from local_llm_server.hardware_evidence_review import review_hardware_evidence

    review = review_hardware_evidence([report_a, report_b]).to_public_dict()
    _write(tmp_path / "reclamation-review.json", review)
    _write(
        tmp_path / "resource-policy-smoke.json",
        {
            "success": {
                "admission": "admit",
                "inference_http_status": 200,
                "committed_bytes": 1024,
                "committed_bytes_after_unload": 0,
                "reserved_bytes_after_unload": 0,
                "health_ok_after_unload": True,
                "health_state_after_unload": "cold",
            },
            "rejection": {"admission": "reject", "backend_load_reached": False},
            "automatic_eviction_exercised": False,
        },
    )

    summary = validate_hardware_bundle(tmp_path)

    assert summary["complete"] is True
    assert summary["gates"] == {
        "thinking_on_off": True,
        "evaluation_repeat": True,
        "reclamation": True,
        "resource_policy_smoke": True,
    }
    assert summary["errors"] == []
    rendered = json.dumps(summary)
    assert str(tmp_path) not in rendered
    assert "prompt" not in rendered.lower()
    assert "production_safety_claim" in rendered


def test_hardware_bundle_rejects_non_comparable_evaluation_and_backend_reach(tmp_path: Path) -> None:
    _write(
        tmp_path / "thinking-campaign.json",
        {
            "schema_version": 1,
            "complete": True,
            "requests": {
                "off": {"enable_thinking": False, "show_thinking": False},
                "on_hidden": {"enable_thinking": True, "show_thinking": False},
            },
        },
    )
    first = _evaluation("a")
    second = _evaluation("b")
    second["manifest"]["runtime_fingerprint"] = "e" * 64
    _write(tmp_path / "evaluation-off-a.json", first)
    _write(tmp_path / "evaluation-off-b.json", second)
    report = _reclamation_report()
    _write(tmp_path / "reclamation-a.json", report)
    _write(tmp_path / "reclamation-b.json", report)
    from local_llm_server.hardware_evidence_review import review_hardware_evidence
    _write(tmp_path / "reclamation-review.json", review_hardware_evidence([report, report]).to_public_dict())
    _write(
        tmp_path / "resource-policy-smoke.json",
        {
            "success": {
                "admission": "admit",
                "inference_http_status": 200,
                "committed_bytes": 1,
                "committed_bytes_after_unload": 0,
                "reserved_bytes_after_unload": 0,
                "health_ok_after_unload": True,
                "health_state_after_unload": "cold",
            },
            "rejection": {"admission": "reject", "backend_load_reached": True},
            "automatic_eviction_exercised": False,
        },
    )

    summary = validate_hardware_bundle(tmp_path)

    assert summary["complete"] is False
    assert summary["gates"]["evaluation_repeat"] is False
    assert summary["gates"]["resource_policy_smoke"] is False
    assert any("attribution-safe" in error for error in summary["errors"])
    assert any("before backend load" in error for error in summary["errors"])


def _accessibility() -> dict:
    check_ids = [
        "keyboard-primary-shell",
        "focus-order-and-visibility",
        "accessibility-tree-or-screen-reader",
        "zoom-and-text-scaling",
        "reduced-motion",
        "error-loading-empty-disabled-states",
    ]
    return {
        "schema_version": 1,
        "evidence_kind": "manual_accessibility",
        "study_id": "a11y-2026-08-18-01",
        "source_revision": "a" * 40,
        "checks": [
            {
                "check_id": check_id,
                "outcome": "pass",
                "severity": "none",
                "sanitized_observation": "Primary interaction remained understandable for this check.",
            }
            for check_id in check_ids
        ],
    }


def _usability() -> dict:
    journeys = [
        "control-plane-status-and-navigation",
        "chat-inference-and-recovery",
        "advanced-control-discovery",
        "evidence-interpretation",
    ]
    return {
        "schema_version": 1,
        "evidence_kind": "representative_user_usability",
        "source_revision": "a" * 40,
        "records": [
            {
                "study_id": "ux-2026-08-18-01",
                "journey_id": journey,
                "task_completed": True,
                "needed_recovery": False,
                "assistance_required": False,
                "duration_bucket": "30s-2m",
                "severity": "none",
                "sanitized_observation": "User found the next action without assistance.",
            }
            for journey in journeys
        ],
    }


def test_product_ui_evidence_reports_readiness_without_mutating_baseline() -> None:
    summary = validate_product_ui_evidence(
        accessibility=_accessibility(),
        usability=_usability(),
    )

    assert summary["manual_accessibility"]["evidence_present"] is True
    assert summary["manual_accessibility"]["acceptance_ready"] is True
    assert summary["representative_user_usability"]["evidence_present"] is True
    assert summary["representative_user_usability"]["acceptance_ready"] is True
    assert summary["full_product_ui_evidence_ready"] is True
    assert summary["baseline_mutated"] is False
    assert summary["errors"] == []


def test_product_ui_evidence_rejects_example_private_and_blocking_evidence() -> None:
    accessibility = _accessibility()
    accessibility["study_id"] = "example-a11y"
    accessibility["checks"][0]["outcome"] = "fail"
    accessibility["checks"][0]["severity"] = "high"
    accessibility["checks"][0]["sanitized_observation"] = "See /Users/alice/private.txt"
    usability = _usability()
    usability["records"][0]["email"] = "person@example.com"
    usability["records"][1]["severity"] = "critical"

    summary = validate_product_ui_evidence(
        accessibility=accessibility,
        usability=usability,
    )

    assert summary["full_product_ui_evidence_ready"] is False
    assert summary["manual_accessibility"]["blocking_findings"] == 1
    assert summary["representative_user_usability"]["blocking_findings"] == 1
    assert any("real non-example" in error for error in summary["errors"])
    assert any("private path" in error for error in summary["errors"])
    assert any("non-allow-listed" in error for error in summary["errors"])
