"""First-class transcription task contracts and resident-runtime execution.

Transcription is intentionally distinct from audio-language chat. A runtime must
explicitly prove the TRANSCRIPTION task; legacy ``audio`` modality metadata alone
never qualifies it as an ASR runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .core.capabilities import descriptor_from_registry_entry
from .core.contracts import ErrorCode, InferenceError, TaskType


@dataclass(frozen=True, slots=True)
class TranscriptionRequest:
    model: str
    audio: bytes
    filename: str | None = None
    language: str | None = None
    prompt: str | None = None

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if not self.audio:
            raise ValueError("audio must be non-empty")


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    model: str
    text: str
    language: str | None = None
    duration_seconds: float | None = None
    segments: tuple[Mapping[str, Any], ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.duration_seconds is not None and self.duration_seconds < 0:
            raise ValueError("duration_seconds must be >= 0 or None")


class TranscriptionEngine(Protocol):
    def transcribe(self, request: Mapping[str, Any]) -> Any: ...


class ResidentTranscriptionService:
    """Execute explicit ASR workloads against currently resident runtimes."""

    def __init__(self, manager: Any) -> None:
        self.manager = manager

    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        try:
            runtime = self.manager.resolve(request.model)
        except LookupError as exc:
            raise InferenceError(
                ErrorCode.MODEL_NOT_RESIDENT,
                "selected transcription model is not resident",
                retryable=True,
                details={"model": request.model},
            ) from exc

        descriptor = descriptor_from_registry_entry(runtime.cfg)
        if TaskType.TRANSCRIPTION not in descriptor.tasks:
            raise InferenceError(
                ErrorCode.UNSUPPORTED_TASK,
                "selected runtime does not expose first-class transcription",
                retryable=False,
                details={
                    "model": runtime.key,
                    "tasks": sorted(task.value for task in descriptor.tasks),
                },
            )

        transcribe = getattr(runtime.engine, "transcribe", None)
        if not callable(transcribe):
            raise InferenceError(
                ErrorCode.UNSUPPORTED_TASK,
                "selected runtime has no transcription execution adapter",
                retryable=False,
                details={"model": runtime.key},
            )

        payload: dict[str, Any] = {"audio": request.audio}
        if request.filename is not None:
            payload["filename"] = request.filename
        if request.language is not None:
            payload["language"] = request.language
        if request.prompt is not None:
            payload["prompt"] = request.prompt

        with self.manager.lease_runtime(runtime):
            try:
                raw = transcribe(payload)
            except InferenceError:
                raise
            except Exception as exc:
                raise InferenceError(
                    ErrorCode.BACKEND_ERROR,
                    "transcription backend execution failed",
                    retryable=False,
                    details={"backend": getattr(runtime.engine, "backend", "unknown")},
                ) from exc

        return _normalize_result(raw, runtime.model_id)


def _normalize_result(raw: Any, model_id: str) -> TranscriptionResult:
    if isinstance(raw, str):
        return TranscriptionResult(model=model_id, text=raw)
    if not isinstance(raw, Mapping):
        raise InferenceError(
            ErrorCode.BACKEND_ERROR,
            "transcription backend returned an unsupported result shape",
        )
    text = raw.get("text")
    if not isinstance(text, str):
        raise InferenceError(
            ErrorCode.BACKEND_ERROR,
            "transcription backend result is missing text",
        )
    language = raw.get("language")
    duration = raw.get("duration_seconds", raw.get("duration"))
    segments_raw = raw.get("segments")
    segments = tuple(
        dict(segment)
        for segment in segments_raw
        if isinstance(segment, Mapping)
    ) if isinstance(segments_raw, (list, tuple)) else ()
    return TranscriptionResult(
        model=model_id,
        text=text,
        language=str(language) if language is not None else None,
        duration_seconds=(
            float(duration) if isinstance(duration, (int, float)) and not isinstance(duration, bool) else None
        ),
        segments=segments,
    )
