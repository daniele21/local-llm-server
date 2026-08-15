from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_evaluation_assets_are_loaded_by_frontend_config():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "/static/control-plane-evaluation.js" in config
    assert "/static/control-plane-evaluation.css" in config
    assert "/static/control-plane-evaluation-history.js" in config
    assert "/static/control-plane-evaluation-history.css" in config


def test_evaluation_ui_uses_real_api_sources_and_valid_sample_multiples():
    script = (STATIC / "control-plane-evaluation.js").read_text(encoding="utf-8")
    assert "/api/v1/evaluation/test-sets" in script
    assert "/api/v1/evaluation/runs" in script
    assert "/v1/models" in script
    assert "value = 10" in script
    assert "value += 10" in script
    assert "No fabricated percentage complete" in script
    assert "runtime_fingerprint" in script
    assert "evidence_grade" in script


def test_evaluation_history_ui_uses_persisted_sources_and_no_better_worse_verdict():
    script = (STATIC / "control-plane-evaluation-history.js").read_text(encoding="utf-8")
    assert "/api/v1/evaluation/history" in script
    assert "/api/v1/evaluation/history/compare" in script
    assert "attribution_safe" in script
    assert "evidence_grade" in script
    assert "Not comparable" in script
    assert "Descriptive only" in script
    assert "Exploratory comparison" in script
    assert "better/worse verdict" in script
    assert "semantic coloring" in script


def test_evaluation_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    for filename in (
        "control-plane-evaluation.js",
        "control-plane-evaluation-history.js",
    ):
        completed = subprocess.run(
            [node, "--check", str(STATIC / filename)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
