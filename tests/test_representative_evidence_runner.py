from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_representative_evidence.py"


def test_representative_evidence_runner_dry_run_is_safe_and_redacts_model_path(tmp_path: Path):
    private_model_path = tmp_path / "private-model.gguf"
    output_dir = tmp_path / "evidence"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dry-run",
            "--model",
            "demo-model",
            "--model-path",
            str(private_model_path),
            "--performance-lab-repo",
            str(tmp_path / "performance-lab"),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["dry_run"] is True
    assert payload["base_url"] == "http://127.0.0.1:1235"
    assert payload["failed_steps"] == []
    assert str(private_model_path) not in completed.stdout

    names = [step["name"] for step in payload["steps"]]
    assert names == [
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

    manifest = json.loads((output_dir / "evidence-manifest.json").read_text(encoding="utf-8"))
    assert manifest == payload
    assert manifest["files"] == []
    assert all("<MODEL_PATH>" in json.dumps(step) or "model-path" not in json.dumps(step) for step in payload["steps"])


def test_representative_evidence_runner_can_plan_without_performance_lab(tmp_path: Path):
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--dry-run",
            "--skip-performance-lab",
            "--model",
            "demo-model",
            "--model-path",
            str(tmp_path / "private-model.gguf"),
            "--output-dir",
            str(tmp_path / "evidence"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert "performance-lab-real-smoke" not in {step["name"] for step in payload["steps"]}
