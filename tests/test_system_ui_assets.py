from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_system_assets_are_loaded_by_frontend_config():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "/static/control-plane-system.js" in config
    assert "/static/control-plane-system.css" in config


def test_settings_and_diagnostics_use_only_real_control_plane_sources():
    script = (STATIC / "control-plane-system.js").read_text(encoding="utf-8")
    for path in (
        "/api/v1/policies",
        "/api/v1/resources",
        "/api/v1/residency",
        "/api/v1/scheduler",
        "/api/v1/evidence",
    ):
        assert path in script
    assert "method: 'POST'" not in script
    assert "read-only" in script


def test_diagnostics_uses_canonical_metric_schema_without_legacy_aliases():
    script = (STATIC / "control-plane-system.js").read_text(encoding="utf-8")
    assert "metrics?.durations_ms" in script
    assert "durations.queue_wait" in script
    assert "durations.ttft" in script
    assert "metrics?.throughput" in script
    assert "throughput.decode_tokens_per_second" in script
    assert "queue_wait_seconds" not in script
    assert "time_to_first_token_seconds" not in script
    assert "output_tokens_per_second" not in script


def test_diagnostics_preserves_legacy_logs_and_unavailable_semantics():
    script = (STATIC / "control-plane-system.js").read_text(encoding="utf-8")
    assert "panel.prepend(surface)" in script
    assert "value === null || value === undefined || value === ''" in script
    assert "return 'Unavailable'" in script
    assert "Prompt and generated content are not copied" in script


def test_settings_exposes_reclamation_boundary_and_policy_truth():
    script = (STATIC / "control-plane-system.js").read_text(encoding="utf-8")
    assert "Remote media default" in script
    assert "Remote model code default" in script
    assert "Evictable now" in script
    assert "do not prove host-memory reclamation" in script


def test_shell_fallbacks_do_not_repeat_obsolete_milestone_blockers():
    shell = (STATIC / "control-plane-shell.js").read_text(encoding="utf-8")
    for stale in (
        "until B1/B2",
        "until C2",
        "No benchmark engine is connected yet",
        "request-path enforcement is still being connected",
        "unavailable until B1/B2/B6",
    ):
        assert stale not in shell
    assert "Loading source-backed Overview state" in shell
    assert "Loading capability-backed endpoint compatibility" in shell
    assert "Loading evaluation sources" in shell
    assert "Loading source-backed policy state" in shell


def test_system_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    for filename in ("control-plane-system.js", "control-plane-shell.js"):
        completed = subprocess.run(
            [node, "--check", str(STATIC / filename)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
