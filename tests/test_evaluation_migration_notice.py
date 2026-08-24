from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_studio_loads_evaluation_migration_notice_asset():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "/static/control-plane-evaluation-migration.js" in config


def test_migration_notice_points_new_work_to_performance_lab_without_disabling_ev3():
    notice = (STATIC / "control-plane-evaluation-migration.js").read_text(encoding="utf-8")
    evaluation = (STATIC / "control-plane-evaluation.js").read_text(encoding="utf-8")

    assert "data-evaluation-migration-notice" in notice
    assert "New evaluation work moves to Performance Lab" in notice
    assert "current EV-3 evidence wave and legacy history" in notice
    assert "New post-cutover evaluation evidence belongs in Performance Lab" in notice
    assert "https://github.com/daniele21/performance-lab" in notice
    assert "MutationObserver" in notice
    assert "evaluationUi" in notice

    # MIG-002 redirect is deliberately non-destructive until EV-3 and the real-runtime
    # replacement evidence are retained.
    assert "/api/v1/evaluation/runs" in evaluation
    assert "/api/v1/evaluation/test-sets" in evaluation


def test_evaluation_migration_notice_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")

    script_path = STATIC / "control-plane-evaluation-migration.js"
    completed = subprocess.run(
        [node, "--check", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
