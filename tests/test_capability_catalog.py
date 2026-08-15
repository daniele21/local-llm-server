from __future__ import annotations

import pytest

from local_llm_server.capability_catalog import (
    capability_catalog_item,
    project_capability_catalog,
    validate_registry_capability_entry,
)


def test_legacy_catalog_projection_is_marked_conservative():
    item = capability_catalog_item(
        "vlm",
        {
            "model_id": "org/vlm",
            "modalities": ["text", "image"],
            "multimodal": True,
        },
    )

    assert item["model_id"] == "org/vlm"
    assert item["capability_source"] == "legacy_conservative"
    assert item["capabilities"]["tasks"] == [
        "chat",
        "structured_generation",
        "vision_language",
    ]


def test_explicit_catalog_projection_is_marked_explicit():
    item = capability_catalog_item(
        "asr",
        {
            "tasks": ["transcription"],
            "input_modalities": ["audio"],
            "output_modalities": ["text"],
            "features": ["streaming"],
        },
    )

    assert item["capability_source"] == "explicit"
    assert item["capabilities"]["tasks"] == ["transcription"]


def test_invalid_explicit_transcription_declaration_fails_before_backend():
    with pytest.raises(ValueError, match="requires audio input"):
        validate_registry_capability_entry(
            {
                "tasks": ["transcription"],
                "input_modalities": ["text"],
                "output_modalities": ["text"],
            }
        )


def test_catalog_projection_is_stably_sorted():
    projected = project_capability_catalog(
        {
            "z": {"modalities": ["text"]},
            "a": {"modalities": ["text"]},
        }
    )

    assert [item["key"] for item in projected] == ["a", "z"]
