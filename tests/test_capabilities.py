from __future__ import annotations

from local_llm_server.core.capabilities import (
    CapabilityFeature,
    Modality,
    descriptor_from_registry_entry,
)
from local_llm_server.core.contracts import GenerationOptions, InferenceRequest, TaskType


def test_text_legacy_entry_maps_to_text_tasks_without_audio_claims():
    descriptor = descriptor_from_registry_entry(
        {"modalities": ["text"], "thinking_mode": "none"}
    )

    assert TaskType.CHAT in descriptor.tasks
    assert TaskType.STRUCTURED_GENERATION in descriptor.tasks
    assert TaskType.TRANSCRIPTION not in descriptor.tasks
    assert descriptor.input_modalities == frozenset({Modality.TEXT})
    assert CapabilityFeature.STRUCTURED_OUTPUT in descriptor.features


def test_image_legacy_entry_maps_to_vision_language():
    descriptor = descriptor_from_registry_entry(
        {"modalities": ["text", "image"], "multimodal": True}
    )

    assert TaskType.VISION_LANGUAGE in descriptor.tasks
    assert Modality.IMAGE in descriptor.input_modalities


def test_audio_modality_does_not_imply_first_class_transcription():
    descriptor = descriptor_from_registry_entry(
        {"modalities": ["text", "audio"], "multimodal": True}
    )

    assert TaskType.TRANSCRIPTION not in descriptor.tasks


def test_explicit_transcription_requires_audio_input():
    try:
        descriptor_from_registry_entry(
            {
                "tasks": ["transcription"],
                "input_modalities": ["text"],
                "output_modalities": ["text"],
            }
        )
    except ValueError as exc:
        assert "requires audio input" in str(exc)
    else:
        raise AssertionError("expected invalid transcription capability to fail")


def test_descriptor_rejects_streaming_when_not_declared():
    descriptor = descriptor_from_registry_entry(
        {
            "tasks": ["chat"],
            "input_modalities": ["text"],
            "output_modalities": ["text"],
            "features": ["structured_output"],
        }
    )
    request = InferenceRequest(
        task=TaskType.CHAT,
        model="demo",
        messages=({"role": "user", "content": "hello"},),
        stream=True,
    )

    assert descriptor.supports(request) is False


def test_thinking_request_requires_thinking_feature():
    descriptor = descriptor_from_registry_entry(
        {"modalities": ["text"], "thinking_mode": "none"}
    )
    request = InferenceRequest(
        task=TaskType.CHAT,
        model="demo",
        messages=({"role": "user", "content": "hello"},),
        generation=GenerationOptions(enable_thinking=True),
    )

    assert descriptor.supports(request) is False


def test_descriptor_serialization_is_stable_and_public_safe():
    descriptor = descriptor_from_registry_entry(
        {"modalities": ["text", "image"], "thinking_mode": "switchable"}
    )

    assert descriptor.to_dict() == {
        "tasks": ["chat", "structured_generation", "vision_language"],
        "input_modalities": ["image", "text"],
        "output_modalities": ["text"],
        "features": ["streaming", "structured_output", "thinking"],
    }
