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


def test_thinking_control_module_is_loaded_by_frontend_config():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "'/static/control-plane-thinking.js'" in config


def test_playground_thinking_off_is_an_explicit_request_not_omission():
    script = (STATIC / "control-plane-thinking.js").read_text(encoding="utf-8")

    assert "payload.enable_thinking = Boolean(enable.checked);" in script
    assert "localStorage.getItem('enable_thinking')" not in script
    assert "mode === 'switchable'" in script
    assert "delete payload.enable_thinking" in script


def test_show_thinking_is_rendering_only_and_independent_from_execution_control():
    script = (STATIC / "control-plane-thinking.js").read_text(encoding="utf-8")

    assert "payload.show_thinking = Boolean(show.checked);" in script
    assert "Display only: does not enable or disable model reasoning." in script
    assert "Controls visibility only; model reasoning execution is unchanged." in script
    # An always-thinking runtime cannot be falsely toggled OFF, but its
    # visibility remains user-controlled.
    assert "if (mode === 'always')" in script
    assert "enable.checked = true;" in script
    assert "enable.disabled = true;" in script
    assert "show.disabled = false;" in script


def test_none_thinking_mode_hides_controls_instead_of_presenting_fake_capability():
    script = (STATIC / "control-plane-thinking.js").read_text(encoding="utf-8")

    assert "if (mode === 'none')" in script
    assert "enableGroup.style.display = 'none';" in script
    assert "showGroup.style.display = 'none';" in script
    assert "capabilities?.thinking_mode" in script


def test_playground_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    for filename in ("app.js", "control-plane-thinking.js"):
        completed = subprocess.run(
            [node, "--check", str(STATIC / filename)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, f"{filename}: {completed.stderr}"
