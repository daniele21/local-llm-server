"""Truthful task-specific metrics for first-class transcription workloads.

ASR evidence is intentionally separate from token-generation metrics. Backend
wall-clock time, audio duration and realtime factor have different semantics
from LLM TTFT/decode throughput and must not be projected into those fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class TranscriptionMetrics:
    backend_wall_clock_ms: float | None = None
    audio_duration_ms: float | None = None
    realtime_factor: float | None = None
    segment_count: int | None = None
    sources: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("backend_wall_clock_ms", self.backend_wall_clock_ms),
            ("audio_duration_ms", self.audio_duration_ms),
            ("realtime_factor", self.realtime_factor),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0 or None")
        if self.segment_count is not None and self.segment_count < 0:
            raise ValueError("segment_count must be >= 0 or None")

    def to_public_dict(self) -> dict[str, object]:
        return {
            "backend_wall_clock_ms": self.backend_wall_clock_ms,
            "audio_duration_ms": self.audio_duration_ms,
            "realtime_factor": self.realtime_factor,
            "segment_count": self.segment_count,
            "sources": dict(self.sources),
        }


def build_transcription_metrics(
    *,
    backend_wall_clock_ms: float | None,
    audio_duration_seconds: float | None,
    segment_count: int | None,
) -> TranscriptionMetrics:
    """Build ASR evidence only from explicitly measured/provided values."""
    wall = _nonnegative_float(backend_wall_clock_ms)
    audio_seconds = _nonnegative_float(audio_duration_seconds)
    audio_ms = audio_seconds * 1000.0 if audio_seconds is not None else None
    segments = (
        segment_count
        if isinstance(segment_count, int)
        and not isinstance(segment_count, bool)
        and segment_count >= 0
        else None
    )

    realtime_factor = None
    if wall is not None and audio_ms is not None and audio_ms > 0:
        realtime_factor = wall / audio_ms

    sources: dict[str, str] = {}
    if wall is not None:
        sources["backend_wall_clock_ms"] = "transcription_service.backend_wall_clock"
    if audio_ms is not None:
        sources["audio_duration_ms"] = "transcription_backend.audio_duration"
    if realtime_factor is not None:
        sources["realtime_factor"] = "backend_wall_clock_ms/audio_duration_ms"
    if segments is not None:
        sources["segment_count"] = "transcription_backend.segments"

    return TranscriptionMetrics(
        backend_wall_clock_ms=wall,
        audio_duration_ms=audio_ms,
        realtime_factor=realtime_factor,
        segment_count=segments,
        sources=sources,
    )


def record_transcription_metrics(runtime: object, metrics: TranscriptionMetrics) -> TranscriptionMetrics:
    runtime.latest_transcription_metrics = metrics
    return metrics


def latest_transcription_metrics(runtime: object) -> TranscriptionMetrics | None:
    value = getattr(runtime, "latest_transcription_metrics", None)
    return value if isinstance(value, TranscriptionMetrics) else None


def _nonnegative_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if number >= 0 else None
