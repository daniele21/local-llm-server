"""Canonical backend-neutral inference types.

These contracts deliberately avoid FastAPI, Pydantic, llama.cpp and MLX types.
They form the stable vocabulary used by API adapters, schedulers, evaluation and
future backend workers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class TaskType(StrEnum):
    CHAT = "chat"
    STRUCTURED_GENERATION = "structured_generation"
    VISION_LANGUAGE = "vision_language"
    TRANSCRIPTION = "transcription"


class TerminationReason(StrEnum):
    STOP = "stop"
    MAX_TOKENS = "max_tokens"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ERROR = "error"


class ErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_TASK = "unsupported_task"
    UNSUPPORTED_MODALITY = "unsupported_modality"
    MODEL_NOT_FOUND = "model_not_found"
    MODEL_NOT_RESIDENT = "model_not_resident"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    BACKEND_ERROR = "backend_error"


@dataclass(frozen=True, slots=True)
class InferenceError(Exception):
    code: ErrorCode
    message: str
    retryable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    repeat_penalty: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    seed: int | None = None
    stop: str | tuple[str, ...] | None = None
    enable_thinking: bool | None = None


@dataclass(frozen=True, slots=True)
class OutputConstraints:
    format: str | None = None
    json_schema: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    task: TaskType
    model: str | None
    messages: tuple[Mapping[str, Any], ...] = ()
    input_text: str | None = None
    generation: GenerationOptions = field(default_factory=GenerationOptions)
    output: OutputConstraints = field(default_factory=OutputConstraints)
    stream: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InferenceResult:
    task: TaskType
    model: str
    content: str
    termination_reason: TerminationReason
    usage: Mapping[str, int | float] = field(default_factory=dict)
    structured_output: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
