from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_playground_formats_structured_api_errors_without_object_stringification():
    script = (STATIC / "app.js").read_text(encoding="utf-8")

    assert "function apiErrorMessage(payload, status)" in script
    assert "Array.isArray(value)" in script
    assert "value.message" in script
    assert "value.code" in script
    assert "apiErrorMessage(errData, response.status)" in script
    assert script.count("apiErrorMessage(err, res.status)") >= 2
    assert "apiErrorMessage({ error: chunk.error }, 500)" in script
    assert "new Error(errData.detail ||" not in script
    assert "new Error(err.detail ||" not in script


def test_playground_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    completed = subprocess.run(
        [node, "--check", str(STATIC / "app.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
