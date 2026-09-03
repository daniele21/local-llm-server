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


def test_registry_validation_rejects_unknown_thinking_mode():
    registry = _registry({
        "one": {
            "filename": "one.gguf",
            "thinking_mode": "sometimes",
        },
    })

    with pytest.raises(ValueError, match="thinking_mode"):
        validate_registry(registry)


def test_registry_validation_accepts_explicit_bounded_generation_domain():
    validate_registry(
        _registry(
            {
                "one": {
                    "filename": "one.gguf",
                    "generation_parameter_domains": {
                        "temperature": {
                            "kind": "float",
                            "minimum": 0.0,
                            "maximum": 0.8,
                            "step": 0.1,
                        }
                    },
                }
            }
        )
    )


def test_registry_validation_rejects_runtime_load_field_as_request_domain():
    registry = _registry(
        {
            "one": {
                "filename": "one.gguf",
                "generation_parameter_domains": {
                    "n_ubatch": {
                        "kind": "integer",
                        "minimum": 64,
                        "maximum": 512,
                    }
                },
            }
        }
    )

    with pytest.raises(ValueError, match="n_ubatch"):
        validate_registry(registry)
