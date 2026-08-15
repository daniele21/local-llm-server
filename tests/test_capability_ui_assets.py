from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_capability_assets_are_loaded_by_frontend_config():
    config = (STATIC / "config.js").read_text(encoding="utf-8")
    assert "/static/control-plane-capabilities.js" in config
    assert "/static/control-plane-capabilities.css" in config


def test_capability_ui_consumes_server_owned_descriptors_and_real_endpoints():
    script = (STATIC / "control-plane-capabilities.js").read_text(encoding="utf-8")
    assert "/v1/models" in script
    assert "/api/v1/models/registry" in script
    assert "/v1/chat/completions" in script
    assert "/v1/audio/transcriptions" in script
    assert "item.capabilities" in script
    assert "input_modalities" in script
    assert "output_modalities" in script
    assert "features" in script


def test_capability_ui_uses_canonical_task_and_feature_names():
    script = (STATIC / "control-plane-capabilities.js").read_text(encoding="utf-8")
    for value in (
        "chat",
        "vision_language",
        "structured_generation",
        "transcription",
        "structured_output",
        "thinking",
    ):
        assert value in script


def test_transcription_playground_is_multipart_and_model_explicit():
    script = (STATIC / "control-plane-capabilities.js").read_text(encoding="utf-8")
    assert "new FormData()" in script
    assert "body.append('file', file)" in script
    assert "body.append('model', record.key || record.modelId)" in script
    assert "MAX_AUDIO_BYTES = 100 * 1024 * 1024" in script


def test_capability_fallback_restores_controls_when_metadata_is_missing():
    script = (STATIC / "control-plane-capabilities.js").read_text(encoding="utf-8")
    assert "setCapabilityControlledState(null)" in script
    assert "capabilityOriginalDisabled" in script
    assert "capabilityOriginalDisplay" in script
    assert "capabilityOriginalPlaceholder" in script
    assert "restoreCapabilityControl" in script
    assert "Legacy Playground behavior is preserved" in script


def test_capability_ui_does_not_encode_named_model_allowlists():
    script = (STATIC / "control-plane-capabilities.js").read_text(encoding="utf-8").lower()
    for model_name in ("llama", "qwen", "gemma", "mistral", "phi", "whisper"):
        assert model_name not in script


def test_capability_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    completed = subprocess.run(
        [node, "--check", str(STATIC / "control-plane-capabilities.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
