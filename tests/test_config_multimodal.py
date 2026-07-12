from __future__ import annotations

from local_llm_server.config import build_config


def test_multimodal_config_resolves_projector():
    cfg = build_config(model="qwen3-vl-4b")

    assert cfg["backend"] == "mlx_vlm_server"
    assert cfg["multimodal"] is True
    assert "image" in cfg["modalities"]
    assert cfg["ctx_size"] == 8192
    assert cfg["model_path"].endswith("Qwen3-VL-4B-Instruct-MLX-4bit")
    assert cfg["mmproj_path"] is None
