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
    assert "/static/control-plane-evaluation-reasoning.js" in config


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


def test_evaluation_ui_supports_source_backed_custom_dataset_import_and_versions():
    script = (STATIC / "control-plane-evaluation.js").read_text(encoding="utf-8")
    assert "/api/v1/evaluation/test-sets/import" in script
    assert "new FormData()" in script
    assert "body.append('file', file)" in script
    assert "test_set_version" in script
    assert "data-version" in script
    assert "data-source" in script
    assert "Duplicate id/version imports are rejected" in script
    assert "Dataset already exists" in script
    assert "body.append('replace'" not in script


def test_evaluation_reasoning_ui_sends_explicit_policy_and_surfaces_effective_profile():
    script = (STATIC / "control-plane-evaluation-reasoning.js").read_text(encoding="utf-8")
    assert "data-evaluation-reasoning-policy" in script
    assert '<option value="off">Off</option>' in script
    assert '<option value="on">On</option>' in script
    assert '<option value="runtime_default">Runtime default</option>' in script
    assert "payload.reasoning_policy = select.value" in script
    assert "default_reasoning_policy" in script
    assert "requested)} requested → ${escapeHtml(latestRunProfile.effective)} effective" in script
    assert "Reasoning ${profile.requested} → ${profile.effective}" in script


def test_evaluation_history_ui_uses_persisted_sources_without_auto_verdicts():
    script = (STATIC / "control-plane-evaluation-history.js").read_text(encoding="utf-8")
    assert "/api/v1/evaluation/history" in script
    assert "/api/v1/evaluation/history/compare" in script
    assert "attribution_safe" in script
    assert "evidence_grade" in script
    assert "Not comparable" in script
    assert "Descriptive only" in script
    assert "Exploratory comparison" in script
    assert "better/worse verdict" in script
    assert "without semantic coloring" in script


def test_reasoning_history_overlay_requires_profile_plus_fingerprint_for_evidence_grade():
    script = (STATIC / "control-plane-evaluation-reasoning.js").read_text(encoding="utf-8")
    assert "Boolean(summary.runtime_fingerprint) && Boolean(profile)" in script
    assert "identityKnown ? 'Evidence-grade' : 'Exploratory'" in script
    assert "historyProfiles" in script


def test_evaluation_history_preserves_unavailable_and_refresh_state_semantics():
    script = (STATIC / "control-plane-evaluation-history.js").read_text(encoding="utf-8")
    assert "value === null || value === undefined || value === ''" in script
    assert "?.innerHTML || ''" in script
    assert "?.outerHTML" not in script
    assert "restoreSelection" in script


def test_evaluation_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    for filename in (
        "control-plane-evaluation.js",
        "control-plane-evaluation-history.js",
        "control-plane-evaluation-reasoning.js",
    ):
        completed = subprocess.run(
            [node, "--check", str(STATIC / filename)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, f"{filename}: {completed.stderr}"
