from __future__ import annotations

from local_llm_server.config import build_config
from local_llm_server import list_models


def test_multimodal_config_resolves_projector():
    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["backend"] == "mlx_vlm_server"
    assert cfg["multimodal"] is True
    assert "image" in cfg["modalities"]
    assert cfg["ctx_size"] == 8192
    assert cfg["max_concurrent_requests"] == 2
    assert cfg["model_path"] == "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    assert cfg["mmproj_path"] is None


def test_environment_backend_overrides_registry(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_BACKEND", "llama_server")

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["backend"] == "llama_server"


def test_float_environment_values_are_parsed(monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_DEFAULT_TEMPERATURE", "0.25")

    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["default_temperature"] == 0.25
    assert isinstance(cfg["default_temperature"], float)


def test_huggingface_model_can_be_listed_without_local_path():
    qwen = next(model for model in list_models() if model["key"] == "qwen3-vl-4b")

    assert qwen["path"] == "mlx-community/Qwen3-VL-4B-Instruct-4bit"
    assert isinstance(qwen["downloaded"], bool)
