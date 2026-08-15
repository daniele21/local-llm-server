from __future__ import annotations

import pytest

from local_llm_server.core.contracts import ErrorCode, InferenceError
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


class _AudioChatEngine:
    backend = "fake_audio_chat"

    def close(self):
        pass


def _explicit_asr_manager():
    engine = _AsrEngine()
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
    manager = ModelRuntimeManager(default_model="asr")
    manager.add(cfg, engine)
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
