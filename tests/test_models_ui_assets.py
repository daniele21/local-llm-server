from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_models_ui_consumes_live_resource_identity_and_residency_sources():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "/v1/models" in script
    assert "/status" in script
    assert "/api/v1/models/registry" in script
    assert "/api/v1/resources" in script
    assert "/api/v1/evidence" in script
    assert "/api/v1/residency" in script
    assert "Unavailable until B1/B2" not in script
    assert "Unavailable until D3" not in script


def test_models_ui_owns_lifecycle_actions_without_legacy_scroll_seam():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "/api/v1/models/load" in script
    assert "/api/v1/models/activate" in script
    assert "method: 'DELETE'" in script
    assert "data-load-model" in script
    assert "data-unload-model" in script
    assert "data-set-default-model" in script
    assert "data-scroll-legacy-model-controls" not in script
    assert "Open lifecycle controls" not in script


def test_models_ui_explains_resource_accounting_and_load_feasibility_truthfully():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "Memory & Residency" in script
    assert "Configured accounting envelope" in script
    assert "estimate_bytes" in script
    assert "Estimated requirement" in script
    assert "Additional capacity required" in script
    assert "this is not a physical-memory observation" in script
    assert "observed footprint" not in script.lower()


def test_models_ui_pinning_is_server_backed_and_not_a_reclamation_claim():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "/api/v1/residency/pin" in script
    assert "data-pin-model" in script
    assert "data-pin-next" in script
    assert "evictable" in script
    assert "last_used_age_seconds" in script
    assert "automatic-eviction eligibility only" in script
    assert "reclaim" not in script.lower()


def test_models_ui_preserves_unavailable_values_instead_of_coercing_to_zero():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "value === null || value === undefined || value === ''" in script
    assert "return 'Unavailable'" in script
    assert "Number(null)" not in script


def test_models_ui_exposes_verified_fingerprint_or_exploratory_state():
    script = (STATIC / "control-plane-models.js").read_text(encoding="utf-8")
    assert "identity?.fingerprint" in script
    assert "shortFingerprint" in script
    assert "Exploratory" in script
    assert "Evidence available" in script


def test_models_ui_css_is_loaded_by_frontend_config():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "/static/control-plane-models.css" in config


def test_models_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    completed = subprocess.run(
        [node, "--check", str(STATIC / "control-plane-models.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
