from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEWER = ROOT / "scripts" / "review_representative_evidence.py"
FINGERPRINT = "a" * 64
TEST_SET_IDENTITY = "b" * 64


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _chat(content: str) -> dict[str, object]:
    return {
        "id": "chatcmpl-test",
        "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
    }


def _ev3(run_id: str, *, failures: int = 0) -> dict[str, object]:
    sample_ids = [f"sample-{index:02d}" for index in range(10)]
    results = []
    for index, sample_id in enumerate(sample_ids):
        succeeded = index >= failures
        results.append(
            {
                "sample_id": sample_id,
                "succeeded": succeeded,
                "scores": [
                    {
                        "name": "deterministic_objective",
                        "value": 1.0 if succeeded else 0.0,
                        "passed": succeeded,
                        "details": {},
                    }
                ],
                "error_code": None if succeeded else "backend_error",
                "metrics": {"wall_time_seconds": 0.5},
            }
        )
    return {
        "evidence_grade": True,
        "report": {
            "manifest": {
                "run_id": run_id,
                "test_set_id": "general-purpose",
                "test_set_version": "1.0.0",
                "test_set_identity": TEST_SET_IDENTITY,
                "sample_ids": sample_ids,
                "model": "demo-model",
                "task_types": ["chat", "structured_generation"],
                "seed": 0,
                "runtime_fingerprint": FINGERPRINT,
                "reasoning_profile": {
                    "requested": "off",
                    "runtime_mode": "switchable",
                    "effective": "off",
                    "request_override": False,
                },
                "content_retained": True,
            },
            "complete": True,
            "results": results,
        },
    }


def _populate_complete_evidence(root: Path, *, he_state: str = "consistent_recovery_observed") -> None:
    _write_json(
        root / "runtime-identity.json",
        {
            "protocol_version": "local-llm-identity-v1",
            "server": {"name": "local-llm-server", "version": "0.4.0"},
            "default_model": "demo-model",
            "models": {
                "demo-model": {
                    "model": {
                        "id": "demo-model",
                        "verification": "verified",
                        "artifact_digest": "sha256:" + "c" * 64,
                    },
                    "runtime": {
                        "name": "llama_cpp",
                        "version": "0.3.0",
                        "fingerprint": FINGERPRINT,
                        "evidence_grade": "verified",
                    },
                    "hardware": {"system": "darwin", "machine": "arm64"},
                }
            },
        },
    )
    _write_json(root / "status-before.json", {"state": "ready"})
    _write_json(root / "status-after-pl.json", {"state": "ready"})
    _write_json(root / "thinking-off-response.json", _chat("Local inference can keep data on-device."))
    _write_json(root / "thinking-on-hidden-response.json", _chat("Local inference can reduce data exposure."))
    _write_json(root / "evaluation-off-a.json", _ev3("ev-a", failures=1))
    _write_json(root / "evaluation-off-b.json", _ev3("ev-b", failures=2))

    pl_dir = root / "performance-lab"
    pl_dir.mkdir(parents=True, exist_ok=True)
    (pl_dir / "runs.sqlite3").write_bytes(b"sqlite-evidence")
    (pl_dir / "run-1.plab.zip").write_bytes(b"portable-bundle")
    _write_json(
        root / "performance-lab-real-smoke.stdout.txt",
        {
            "probe": {"healthy": True, "models": ["demo-model"]},
            "run": {
                "run_id": "pl-run-1",
                "status": "succeeded",
                "fingerprint_id": "pl-fingerprint-1",
                "store_path": "/Users/private/secret/performance-lab/runs.sqlite3",
                "bundle_path": "/Users/private/secret/performance-lab/run-1.plab.zip",
                "sample_count": 4,
            },
            "config_path": "/Users/private/secret/config.json",
        },
    )

    _write_json(root / "reclamation-a.json", {"schema_version": 1, "private": "raw-a"})
    _write_json(root / "reclamation-b.json", {"schema_version": 1, "private": "raw-b"})
    _write_json(
        root / "reclamation-review.json",
        {
            "state": he_state,
            "report_count": 2,
            "compatible_report_count": 2,
            "total_cycles": 6,
            "complete_windows": 6,
            "error_cycles": 0,
            "observations": {
                "recovery_observed": 6 if he_state != "consistent_no_recovery_observed" else 0,
                "no_recovery_observed": 6 if he_state == "consistent_no_recovery_observed" else 0,
                "inconclusive": 0,
            },
            "identity_grade": "verified",
            "reasons": ["all_conclusive_cycles_observed_recovery"],
            "automatic_eviction_recommendation": "not_provided",
            "production_safety_claim": False,
        },
    )
    _write_json(
        root / "resource-policy-smoke.json",
        {
            "schema_version": 1,
            "procedure": "bounded_resource_policy_smoke",
            "model": "demo-model",
            "backend": "llama_cpp",
            "estimate_bytes": 1024,
            "host_available_before_bytes": 16 * 1024**3,
            "host_safety_bytes": 2 * 1024**3,
            "success_margin_bytes": int(0.5 * 1024**3),
            "headroom_bytes": int(0.5 * 1024**3),
            "success": {
                "admission": "admit",
                "loaded": True,
                "inference_http_status": 200,
                "committed_bytes": 1024,
                "reserved_bytes_after_unload": 0,
                "committed_bytes_after_unload": 0,
                "reservation_count_after_unload": 0,
                "health_ok_after_unload": True,
                "health_state_after_unload": "cold",
            },
            "rejection": {
                "admission": "reject",
                "reason": "configured usable budget would be exceeded",
                "resident_count_after_reject": 0,
                "reservation_count_after_reject": 0,
                "backend_load_reached": False,
            },
            "automatic_eviction_exercised": False,
        },
    )
    (root / "artifact-verification.stdout.txt").write_text("verified\n", encoding="utf-8")
    (root / "artifact-verification.stderr.txt").write_text("", encoding="utf-8")
    (root / "local-llm-server.log").write_text("server log\n", encoding="utf-8")
    (root / "performance-lab-real-smoke.stderr.txt").write_text("", encoding="utf-8")
    for name in ("reclamation-a", "reclamation-b", "reclamation-review", "resource-policy-smoke"):
        (root / f"{name}.stdout.txt").write_text("complete\n", encoding="utf-8")
        (root / f"{name}.stderr.txt").write_text("", encoding="utf-8")

    step_names = [
        "artifact-verification",
        "server",
        "runtime-identity",
        "status-before",
        "thinking-off-response",
        "thinking-on-hidden-response",
        "evaluation-off-a",
        "evaluation-off-b",
        "performance-lab-real-smoke",
        "status-after-pl",
        "server-shutdown",
        "reclamation-a",
        "reclamation-b",
        "reclamation-review",
        "resource-policy-smoke",
    ]
    steps = [{"name": name, "status": "passed"} for name in step_names]
    for step in steps:
        if step["name"] == "server-shutdown":
            step["graceful"] = True
            step["returncode"] = 0

    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "evidence-manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(root)),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    _write_json(
        root / "evidence-manifest.json",
        {
            "schema_version": 1,
            "dry_run": False,
            "model": "demo-model",
            "backend": "llama_cpp",
            "base_url": "http://127.0.0.1:1235",
            "platform": {"system": "Darwin", "machine": "arm64", "python": "3.12.0"},
            "steps": steps,
            "failed_steps": [],
            "files": files,
        },
    )


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REVIEWER), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_reviewer_emits_public_safe_ready_summary_for_complete_evidence(tmp_path: Path):
    _populate_complete_evidence(tmp_path)
    completed = _run(tmp_path)

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["overall_state"] == "ready_for_mig003"
    assert {check["state"] for check in payload["checks"]} == {"pass"}
    assert payload["model"] == "demo-model"
    assert FINGERPRINT in completed.stdout
    assert "/Users/private/secret" not in completed.stdout
    assert "Local inference can" not in completed.stdout
    assert (tmp_path / "representative-review.json").is_file()

    ev3 = next(check for check in payload["checks"] if check["id"] == "ev3")
    assert ev3["evidence"]["run_a"]["failure_count"] == 1
    assert ev3["evidence"]["run_b"]["failure_count"] == 2
    assert ev3["evidence"]["comparable"] is True


def test_reviewer_blocks_if_manifest_inventory_was_modified(tmp_path: Path):
    _populate_complete_evidence(tmp_path)
    (tmp_path / "status-before.json").write_text('{"state":"tampered"}\n', encoding="utf-8")

    completed = _run(tmp_path)
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["overall_state"] == "blocked"
    integrity = next(check for check in payload["checks"] if check["id"] == "manifest_integrity")
    assert integrity["state"] == "blocked"
    assert "status-before.json" in integrity["evidence"]["invalid_files"]


def test_reviewer_keeps_mixed_he2_as_manual_review_not_false_failure(tmp_path: Path):
    _populate_complete_evidence(tmp_path, he_state="mixed")

    completed = _run(tmp_path)
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["overall_state"] == "review_required"
    he2 = next(check for check in payload["checks"] if check["id"] == "he2")
    assert he2["state"] == "review_required"
    assert he2["evidence"]["review_state"] == "mixed"


def test_reviewer_blocks_explicit_thinking_markup_leak(tmp_path: Path):
    _populate_complete_evidence(tmp_path)
    _write_json(tmp_path / "thinking-on-hidden-response.json", _chat("<think>hidden chain</think>final"))
    manifest = _load_manifest(tmp_path)
    _refresh_manifest_file(manifest, tmp_path, "thinking-on-hidden-response.json")
    _write_json(tmp_path / "evidence-manifest.json", manifest)

    completed = _run(tmp_path)
    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    boundary = next(check for check in payload["checks"] if check["id"] == "thinking_boundary")
    assert boundary["state"] == "blocked"
    assert boundary["evidence"]["explicit_thinking_markup_exposed"] is True
    assert "hidden chain" not in completed.stdout


def _load_manifest(root: Path) -> dict[str, Any]:
    return json.loads((root / "evidence-manifest.json").read_text(encoding="utf-8"))


def _refresh_manifest_file(manifest: dict[str, Any], root: Path, relative: str) -> None:
    target = root / relative
    for item in manifest["files"]:
        if item["path"] == relative:
            item["bytes"] = target.stat().st_size
            item["sha256"] = _sha256(target)
            return
    raise AssertionError(f"missing manifest entry: {relative}")
