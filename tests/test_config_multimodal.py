from __future__ import annotations

from pathlib import Path

from local_llm_server.config import build_config
from local_llm_server import list_models


def test_multimodal_config_prefers_complete_lmstudio_model(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    local_model = (
        tmp_path / ".lmstudio" / "models" / "lmstudio-community"
        / "Qwen3-VL-4B-Instruct-MLX-4bit"
    )
    local_model.mkdir(parents=True)
    (local_model / "config.json").write_text("{}")
    (local_model / "model.safetensors").write_bytes(b"weights")

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["backend"] == "mlx_vlm_server"
    assert cfg["multimodal"] is True
    assert "image" in cfg["modalities"]
    assert cfg["ctx_size"] == 8192
    assert cfg["max_concurrent_requests"] == 2
    assert cfg["model_path"] == str(local_model)
    assert cfg["mmproj_path"] is None


def test_multimodal_config_falls_back_to_huggingface(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["model_path"] == "mlx-community/Qwen3-VL-4B-Instruct-4bit"


def test_environment_backend_overrides_registry(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_BACKEND", "llama_server")

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["backend"] == "llama_server"


def test_float_environment_values_are_parsed(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_DEFAULT_TEMPERATURE", "0.25")

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["default_temperature"] == 0.25
    assert isinstance(cfg["default_temperature"], float)


def test_lmstudio_model_can_be_listed_as_downloaded():
    qwen = next(model for model in list_models() if model["key"] == "qwen3-vl-4b")

    assert qwen["path"].endswith("Qwen3-VL-4B-Instruct-MLX-4bit")
    assert qwen["downloaded"] is True
