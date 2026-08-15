from pathlib import Path
from types import SimpleNamespace

import local_llm_server


def test_list_models_exposes_conservative_capability_metadata(monkeypatch, tmp_path: Path):
    registry = {
        "models_dir": tmp_path,
        "models": {
            "text-model": {
                "model_id": "org/text-model",
                "backend": "llama_cpp",
                "modalities": ["text"],
            },
            "vision-model": {
                "model_id": "org/vision-model",
                "backend": "llama_server",
                "multimodal": True,
                "modalities": ["text", "image"],
            },
        },
    }

    monkeypatch.setattr("local_llm_server.registry.load_registry", lambda: registry)
    monkeypatch.setattr(
        "local_llm_server.model_sources.resolve_registry_model",
        lambda key, entry, models_dir, backend=None: SimpleNamespace(
            downloaded=False,
            model_path=f"/models/{key}",
            source_type="unresolved",
            mmproj_path=None,
        ),
    )

    models = {item["key"]: item for item in local_llm_server.list_models()}

    text = models["text-model"]
    assert text["capability_source"] == "legacy_conservative"
    assert "chat" in text["capabilities"]["tasks"]
    assert text["capabilities"]["input_modalities"] == ["text"]

    vision = models["vision-model"]
    assert "vision_language" in vision["capabilities"]["tasks"]
    assert "image" in vision["capabilities"]["input_modalities"]


def test_list_models_preserves_explicit_capability_provenance(monkeypatch, tmp_path: Path):
    registry = {
        "models_dir": tmp_path,
        "models": {
            "explicit": {
                "model_id": "org/explicit",
                "backend": "mlx",
                "tasks": ["chat", "structured_generation"],
                "input_modalities": ["text"],
                "output_modalities": ["text"],
                "features": ["structured_output"],
            }
        },
    }
    monkeypatch.setattr("local_llm_server.registry.load_registry", lambda: registry)
    monkeypatch.setattr(
        "local_llm_server.model_sources.resolve_registry_model",
        lambda key, entry, models_dir, backend=None: SimpleNamespace(
            downloaded=True,
            model_path=f"/models/{key}",
            source_type="explicit",
            mmproj_path=None,
        ),
    )

    [model] = local_llm_server.list_models()
    assert model["capability_source"] == "explicit"
    assert model["capabilities"]["tasks"] == ["chat", "structured_generation"]
    assert model["capabilities"]["output_modalities"] == ["text"]
    assert model["capabilities"]["features"] == ["structured_output"]
