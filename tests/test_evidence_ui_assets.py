from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_overview_consumes_resource_and_evidence_product_sources():
    script = (STATIC / "control-plane-live.js").read_text(encoding="utf-8")
    assert "/api/v1/resources" in script
    assert "/api/v1/evidence" in script
    assert "configured_default_model" in script
    assert "runtime_fingerprint" not in script  # identity uses the canonical fingerprint field
    assert "identity?.fingerprint" in script


def test_overview_preserves_unavailable_semantics_for_unsourced_metrics():
    script = (STATIC / "control-plane-live.js").read_text(encoding="utf-8")
    assert "TTFT" in script
    assert "Unavailable" in script
    assert "decode_tokens_per_second" in script
    assert "output_tokens" in script
    assert "no fallback values are fabricated" in script


def test_overview_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    completed = subprocess.run(
        [node, "--check", str(STATIC / "control-plane-live.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
