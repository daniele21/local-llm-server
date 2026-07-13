from __future__ import annotations

import pytest

from local_llm_server.registry import validate_registry


def _registry(models, *, default_model="one", startup_models=None):
    return {
        "models_dir": "/tmp/models",
        "defaults": {},
        "models": models,
        "default_model": default_model,
        "startup_models": startup_models or [],
    }


def test_registry_validation_rejects_alias_collisions():
    registry = _registry({
        "one": {"filename": "one.gguf", "model_id": "shared"},
        "shared": {"filename": "two.gguf", "model_id": "two"},
    })

    with pytest.raises(ValueError, match="alias 'shared'"):
        validate_registry(registry)


def test_registry_validation_rejects_invalid_multimodal_llama_server():
    registry = _registry({
        "one": {
            "filename": "one.gguf",
            "backend": "llama_server",
            "multimodal": True,
            "modalities": ["text", "image"],
        },
    })

    with pytest.raises(ValueError, match="needs mmproj"):
        validate_registry(registry)


def test_registry_validation_rejects_invalid_runtime_parameters():
    registry = _registry({
        "one": {
            "filename": "one.gguf",
            "params": {"max_concurrent_requests": 0},
        },
    })

    with pytest.raises(ValueError, match="max_concurrent_requests"):
        validate_registry(registry)


def test_registry_validation_accepts_huggingface_vlm_model():
    validate_registry(_registry({
        "vision": {
            "model_id": "mlx-community/example",
            "backend": "mlx_vlm_server",
            "multimodal": True,
            "modalities": ["text", "image"],
            "params": {"max_concurrent_requests": 2},
        },
    }, default_model="vision"))
