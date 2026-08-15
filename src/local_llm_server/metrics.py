"""Canonical, privacy-safe inference metric vocabulary.

The schema keeps duration, token and event semantics explicit. Missing backend
measurements are represented as None rather than zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class RequestPhase(str, Enum):
    ADMITTED = "admitted"
    QUEUED = "queued"
    STARTED = "started"
    FIRST_OUTPUT = "first_output"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LoadKind(str, Enum):
    UNKNOWN = "unknown"
    COLD = "cold"
    WARM = "warm"
    ALREADY_RESIDENT = "already_resident"


class CacheKind(str, Enum):
    UNKNOWN = "unknown"
    MISS = "miss"
    HIT = "hit"
    BYPASSED = "bypassed"


@dataclass(frozen=True, slots=True)
class DurationMetrics:
    queue_wait_ms: float | None = None
    model_load_ms: float | None = None
    prompt_prefill_ms: float | None = None
    ttft_ms: float | None = None
    decode_ms: float | None = None
    total_ms: float | None = None

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items() if hasattr(self, "__dict__") else (
            ("queue_wait_ms", self.queue_wait_ms),
            ("model_load_ms", self.model_load_ms),
            ("prompt_prefill_ms", self.prompt_prefill_ms),
            ("ttft_ms", self.ttft_ms),
            ("decode_ms", self.decode_ms),
            ("total_ms", self.total_ms),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0 or None")


@dataclass(frozen=True, slots=True)
class CountMetrics:
    input_tokens: int | None = None
    output_tokens: int | None = None
    output_chunks: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("output_chunks", self.output_chunks),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0 or None")

    @property
    def generated_tokens(self) -> int | None:
        """True token count only; chunks are never substituted for tokens."""
        return self.output_tokens


@dataclass(frozen=True, slots=True)
class ThroughputMetrics:
    decode_tokens_per_second: float | None = None
    output_chunks_per_second: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("decode_tokens_per_second", self.decode_tokens_per_second),
            ("output_chunks_per_second", self.output_chunks_per_second),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0 or None")


@dataclass(frozen=True, slots=True)
class InferenceMetrics:
    durations: DurationMetrics = field(default_factory=DurationMetrics)
    counts: CountMetrics = field(default_factory=CountMetrics)
    throughput: ThroughputMetrics = field(default_factory=ThroughputMetrics)
    load_kind: LoadKind = LoadKind.UNKNOWN
    cache_kind: CacheKind = CacheKind.UNKNOWN
    termination_reason: str | None = None
    resource_snapshot_id: str | None = None
    sources: Mapping[str, str] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, object]:
        """Serialize metric values without prompt/output content."""
        return {
            "durations_ms": {
                "queue_wait": self.durations.queue_wait_ms,
                "model_load": self.durations.model_load_ms,
                "prompt_prefill": self.durations.prompt_prefill_ms,
                "ttft": self.durations.ttft_ms,
                "decode": self.durations.decode_ms,
                "total": self.durations.total_ms,
            },
            "counts": {
                "input_tokens": self.counts.input_tokens,
                "output_tokens": self.counts.output_tokens,
                "output_chunks": self.counts.output_chunks,
            },
            "throughput": {
                "decode_tokens_per_second": self.throughput.decode_tokens_per_second,
                "output_chunks_per_second": self.throughput.output_chunks_per_second,
            },
            "load_kind": self.load_kind.value,
            "cache_kind": self.cache_kind.value,
            "termination_reason": self.termination_reason,
            "resource_snapshot_id": self.resource_snapshot_id,
            "sources": dict(self.sources),
        }
