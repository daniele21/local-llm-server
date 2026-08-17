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
    assert "data-evaluation-retain-content" in script
    assert "retain_content:" in script
    assert 'type="checkbox" checked' in script
    assert "Save model outputs in local history" in script


def test_evaluation_ui_exposes_progressive_sample_details():
    script = (STATIC / "control-plane-evaluation.js").read_text(encoding="utf-8")
    history = (STATIC / "control-plane-evaluation-history.js").read_text(encoding="utf-8")
    assert "data-sample-details-toggle" in script
    assert 'aria-expanded="false"' in script
    assert "Prompt" in script
    assert "Expected" in script
    assert "Model output" in script
    assert "Raw metrics" in script
    assert "Model output was not saved" in script
    assert "window.localLlmEvaluationUi" in script
    assert "sampleUi.renderSampleRows" in history
    assert "content_retained" in history
    assert "dataset_context" in history
    assert "detailHtml" in history
    assert "focusedDetailControl" in history
    assert "data-evaluation-history-close" in history


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


def test_evaluation_reasoning_policy_bootstrap_is_not_fetch_order_dependent():
    script = (STATIC / "control-plane-evaluation-reasoning.js").read_text(encoding="utf-8")
    assert "function ingestPolicies(payload)" in script
    assert "async function refreshPolicies()" in script
    assert "await baseFetch(TEST_SETS" in script
    assert "ingestPolicies(await response.json())" in script
    assert "refreshPolicies();" in script


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


def test_reasoning_history_identity_decoration_is_idempotent_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    script_path = STATIC / "control-plane-evaluation-reasoning.js"
    harness = r"""
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const noop = () => {};
const windowObject = {
    fetch: async () => ({ ok: false }),
    addEventListener: noop,
    dispatchEvent: noop,
};
const context = {
    window: windowObject,
    document: {
        readyState: 'loading',
        addEventListener: noop,
        querySelector: () => null,
        querySelectorAll: () => [],
    },
    MutationObserver: class { observe() {} },
    CustomEvent: class {},
    URL,
    Map,
    setTimeout,
};
vm.runInNewContext(source, context);
const update = windowObject.localLlmEvaluationReasoning.updateHistoryIdentityCell;
let writes = 0;
const cell = {
    value: '',
    get innerHTML() { return this.value; },
    set innerHTML(value) { writes += 1; this.value = value; },
};
if (update(cell, false) !== true) throw new Error('first decoration must mutate');
if (update(cell, false) !== false) throw new Error('same state must not mutate');
if (writes !== 1) throw new Error(`expected one write, got ${writes}`);
if (update(cell, true) !== true) throw new Error('changed state must mutate');
if (update(cell, true) !== false) throw new Error('stable changed state must not mutate');
if (writes !== 2) throw new Error(`expected two writes, got ${writes}`);
"""
    completed = subprocess.run(
        [node, "-e", harness, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


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
