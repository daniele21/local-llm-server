from __future__ import annotations

from local_llm_server.live_evidence import runtime_evidence_payload
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.transcription import ResidentTranscriptionService, TranscriptionRequest
from local_llm_server.transcription_metrics import (
    TranscriptionMetrics,
    build_transcription_metrics,
    latest_transcription_metrics,
)


class _AsrEngine:
    backend = "fake_asr"

    def transcribe(self, payload):
        return {
            "text": "hello",
            "duration_seconds": 2.0,
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "hel"},
                {"start": 1.0, "end": 2.0, "text": "lo"},
            ],
            "metadata": {"backend_field": "kept-on-result"},
        }

    def close(self):
        pass


def _manager():
    manager = ModelRuntimeManager(default_model="asr")
    runtime = manager.add(
        {
            "model": "asr",
            "model_id": "org/asr",
            "backend": "fake_asr",
            "tasks": ["transcription"],
            "input_modalities": ["audio"],
            "output_modalities": ["text"],
            "modalities": ["audio"],
            "max_concurrent_requests": 1,
        },
        _AsrEngine(),
    )
    return manager, runtime


def test_builder_keeps_asr_semantics_separate_from_generation_metrics():
    metrics = build_transcription_metrics(
        backend_wall_clock_ms=500.0,
        audio_duration_seconds=2.0,
        segment_count=3,
    )

    assert metrics == TranscriptionMetrics(
        backend_wall_clock_ms=500.0,
        audio_duration_ms=2000.0,
        realtime_factor=0.25,
        segment_count=3,
        sources={
            "backend_wall_clock_ms": "transcription_service.backend_wall_clock",
            "audio_duration_ms": "transcription_backend.audio_duration",
            "realtime_factor": "backend_wall_clock_ms/audio_duration_ms",
            "segment_count": "transcription_backend.segments",
        },
    )
    public = metrics.to_public_dict()
    assert "tokens" not in str(public).lower()
    assert "ttft" not in str(public).lower()


def test_builder_does_not_invent_realtime_factor_without_positive_audio_duration():
    zero_audio = build_transcription_metrics(
        backend_wall_clock_ms=100.0,
        audio_duration_seconds=0.0,
        segment_count=None,
    )
    missing_audio = build_transcription_metrics(
        backend_wall_clock_ms=100.0,
        audio_duration_seconds=None,
        segment_count=-1,
    )

    assert zero_audio.audio_duration_ms == 0.0
    assert zero_audio.realtime_factor is None
    assert missing_audio.audio_duration_ms is None
    assert missing_audio.realtime_factor is None
    assert missing_audio.segment_count is None


def test_service_records_backend_wall_clock_after_success_and_preserves_metadata():
    manager, runtime = _manager()
    times = iter((10.0, 10.5))
    result = ResidentTranscriptionService(
        manager,
        clock=lambda: next(times),
    ).transcribe(
        TranscriptionRequest(model="asr", audio=b"audio")
    )

    assert result.metadata == {"backend_field": "kept-on-result"}
    metrics = latest_transcription_metrics(runtime)
    assert metrics is not None
    assert metrics.backend_wall_clock_ms == 500.0
    assert metrics.audio_duration_ms == 2000.0
    assert metrics.realtime_factor == 0.25
    assert metrics.segment_count == 2


def test_live_evidence_exposes_asr_metrics_under_task_specific_namespace():
    manager, runtime = _manager()
    times = iter((2.0, 2.4))
    ResidentTranscriptionService(manager, clock=lambda: next(times)).transcribe(
        TranscriptionRequest(model="asr", audio=b"audio")
    )

    payload = runtime_evidence_payload(runtime)
    task = payload["task_metrics"]["transcription"]

    assert round(task["backend_wall_clock_ms"], 6) == 400.0
    assert task["audio_duration_ms"] == 2000.0
    assert round(task["realtime_factor"], 6) == 0.2
    assert task["segment_count"] == 2
    # The generation metric namespace remains independent rather than being
    # filled with ASR pseudo-token values.
    assert payload["metrics"]["counts"]["output_tokens"] is None
