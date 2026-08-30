from __future__ import annotations

import pytest

from local_llm_server.core.contracts import ErrorCode, InferenceError
from local_llm_server.resource_manager import ReservationKind, ResourceManager
from local_llm_server.resources import ResourceBudget
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.transcription import ResidentTranscriptionService, TranscriptionRequest


class _AsrEngine:
    backend = "fake_asr"

    def __init__(self):
        self.calls = 0
        self.payload = None

    def transcribe(self, payload):
        self.calls += 1
        self.payload = payload
        return {
            "text": "hello world",
            "language": "en",
            "duration": 1.25,
            "segments": [{"start": 0.0, "end": 1.25, "text": "hello world"}],
        }

    def close(self):
        pass


class _ResourceAwareAsrEngine(_AsrEngine):
    def __init__(self, resources: ResourceManager):
        super().__init__()
        self.resources = resources
        self.saw_transient_reservation = False

    def transcribe(self, payload):
        self.saw_transient_reservation = (
            len(self.resources.snapshot(kind=ReservationKind.TRANSIENT)) == 1
        )
        return super().transcribe(payload)


class _AudioChatEngine:
    backend = "fake_audio_chat"

    def close(self):
        pass


def _asr_cfg(**overrides):
    cfg = {
        "model": "asr",
        "model_id": "org/asr",
        "backend": "fake_asr",
        "modalities": ["audio", "text"],
        "tasks": ["transcription"],
        "input_modalities": ["audio"],
        "output_modalities": ["text"],
        "features": ["streaming"],
        "max_concurrent_requests": 1,
    }
    cfg.update(overrides)
    return cfg


def _explicit_asr_manager():
    engine = _AsrEngine()
    manager = ModelRuntimeManager(default_model="asr")
    manager.add(_asr_cfg(), engine)
    return manager, engine


def test_explicit_transcription_runtime_executes_asr_task():
    manager, engine = _explicit_asr_manager()
    result = ResidentTranscriptionService(manager).transcribe(
        TranscriptionRequest(
            model="asr",
            audio=b"RIFFfake",
            filename="meeting.wav",
            language="en",
        )
    )

    assert result.model == "org/asr"
    assert result.text == "hello world"
    assert result.language == "en"
    assert result.duration_seconds == 1.25
    assert len(result.segments) == 1
    assert engine.calls == 1
    assert engine.payload["audio"] == b"RIFFfake"
    assert engine.payload["filename"] == "meeting.wav"


def test_transcription_holds_transient_reservation_through_backend_execution():
    resources = ResourceManager(ResourceBudget(limit_bytes=100))
    engine = _ResourceAwareAsrEngine(resources)
    manager = ModelRuntimeManager(default_model="asr", resource_manager=resources)
    manager.add(_asr_cfg(resource_request_estimate_bytes=60), engine)

    result = ResidentTranscriptionService(manager).transcribe(
        TranscriptionRequest(model="asr", audio=b"audio")
    )

    assert result.text == "hello world"
    assert engine.saw_transient_reservation is True
    assert resources.snapshot() == ()


def test_transcription_rejects_peak_before_backend_execution():
    resources = ResourceManager(ResourceBudget(limit_bytes=100))
    engine = _AsrEngine()
    manager = ModelRuntimeManager(default_model="asr", resource_manager=resources)
    manager.add(_asr_cfg(resource_request_estimate_bytes=60), engine)
    resources.reserve("runtime:other", 50, kind=ReservationKind.RESIDENT)
    resources.commit("runtime:other")

    with pytest.raises(InferenceError) as exc_info:
        ResidentTranscriptionService(manager).transcribe(
            TranscriptionRequest(model="asr", audio=b"audio")
        )

    assert exc_info.value.code is ErrorCode.RESOURCE_EXHAUSTED
    assert exc_info.value.retryable is True
    assert engine.calls == 0
    [resident] = resources.snapshot()
    assert resident.kind is ReservationKind.RESIDENT
    assert resident.accounted_bytes == 50


def test_transcription_input_multiplier_accounts_audio_bytes():
    resources = ResourceManager(ResourceBudget(limit_bytes=100))
    engine = _ResourceAwareAsrEngine(resources)
    manager = ModelRuntimeManager(default_model="asr", resource_manager=resources)
    manager.add(
        _asr_cfg(
            resource_request_base_bytes=10,
            resource_request_input_byte_multiplier=2,
            resource_request_safety_margin_bytes=5,
        ),
        engine,
    )

    ResidentTranscriptionService(manager).transcribe(
        TranscriptionRequest(model="asr", audio=b"12345678")
    )

    assert engine.saw_transient_reservation is True
    assert resources.snapshot() == ()


def test_legacy_audio_modality_does_not_imply_transcription():
    engine = _AudioChatEngine()
    cfg = {
        "model": "audio-chat",
        "model_id": "org/audio-chat",
        "backend": "fake_audio_chat",
        "modalities": ["text", "audio"],
        "max_concurrent_requests": 1,
    }
    manager = ModelRuntimeManager(default_model="audio-chat")
    manager.add(cfg, engine)

    with pytest.raises(InferenceError) as exc_info:
        ResidentTranscriptionService(manager).transcribe(
            TranscriptionRequest(model="audio-chat", audio=b"audio")
        )

    assert exc_info.value.code is ErrorCode.UNSUPPORTED_TASK
    assert "transcription" not in exc_info.value.details["tasks"]


def test_transcription_requires_resident_model():
    manager = ModelRuntimeManager()
    with pytest.raises(InferenceError) as exc_info:
        ResidentTranscriptionService(manager).transcribe(
            TranscriptionRequest(model="missing", audio=b"audio")
        )
    assert exc_info.value.code is ErrorCode.MODEL_NOT_RESIDENT


def test_explicit_transcription_without_engine_adapter_fails_typed():
    engine = _AudioChatEngine()
    cfg = {
        "model": "declared-asr",
        "model_id": "org/declared-asr",
        "backend": "fake",
        "tasks": ["transcription"],
        "input_modalities": ["audio"],
        "output_modalities": ["text"],
        "features": ["streaming"],
        "max_concurrent_requests": 1,
    }
    manager = ModelRuntimeManager(default_model="declared-asr")
    manager.add(cfg, engine)

    with pytest.raises(InferenceError) as exc_info:
        ResidentTranscriptionService(manager).transcribe(
            TranscriptionRequest(model="declared-asr", audio=b"audio")
        )
    assert exc_info.value.code is ErrorCode.UNSUPPORTED_TASK
    assert "adapter" in exc_info.value.message


def test_empty_audio_is_rejected_at_contract_boundary():
    with pytest.raises(ValueError, match="audio must be non-empty"):
        TranscriptionRequest(model="asr", audio=b"")
