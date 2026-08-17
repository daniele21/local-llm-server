"""Evaluation and test-set contracts independent from runtime execution.

D4a defines reproducible dataset, selection, scoring and report identity. The
later D4 execution engine attaches exact runtime fingerprints and measured
metrics before comparisons are considered evidence-grade.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from .core.contracts import InferenceResult, TaskType


@dataclass(frozen=True, slots=True)
class EvaluationSample:
    sample_id: str
    task: TaskType
    payload: Mapping[str, Any]
    expected: Mapping[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.sample_id.strip():
            raise ValueError("sample_id must be non-empty")

    def identity_payload(self) -> dict[str, object]:
        """Canonical content that determines evaluation semantics."""
        return {
            "sample_id": self.sample_id,
            "task": self.task.value,
            "payload": dict(self.payload),
            "expected": dict(self.expected),
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class TestSet:
    test_set_id: str
    version: str
    samples: tuple[EvaluationSample, ...]
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.test_set_id.strip() or not self.version.strip():
            raise ValueError("test_set_id and version must be non-empty")
        if not self.samples:
            raise ValueError("test set must contain at least one sample")
        ids = [sample.sample_id for sample in self.samples]
        if len(ids) != len(set(ids)):
            raise ValueError("sample_id values must be unique within a test set")

    @property
    def identity(self) -> str:
        payload = {
            "test_set_id": self.test_set_id,
            "version": self.version,
            "samples": [
                sample.identity_payload()
                for sample in sorted(self.samples, key=lambda item: item.sample_id)
            ],
            "provenance": dict(self.provenance),
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SampleSelection:
    limit: int | None = None
    seed: int = 0

    def __post_init__(self) -> None:
        if self.limit is not None and self.limit < 1:
            raise ValueError("limit must be >= 1 or None")

    def select(self, test_set: TestSet) -> tuple[EvaluationSample, ...]:
        ordered = sorted(test_set.samples, key=lambda sample: sample.sample_id)
        if self.limit is None or self.limit >= len(ordered):
            return tuple(ordered)
        rng = random.Random(self.seed)
        selected = rng.sample(ordered, self.limit)
        return tuple(sorted(selected, key=lambda sample: sample.sample_id))


@dataclass(frozen=True, slots=True)
class Score:
    name: str
    value: float | None
    passed: bool | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


class Scorer(Protocol):
    name: str

    def score(self, sample: EvaluationSample, result: InferenceResult) -> Score: ...


@dataclass(frozen=True, slots=True)
class EvaluationRunManifest:
    run_id: str
    test_set_id: str
    test_set_version: str
    test_set_identity: str
    sample_ids: tuple[str, ...]
    model: str
    task_types: tuple[TaskType, ...]
    seed: int
    runtime_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.model.strip():
            raise ValueError("run_id and model must be non-empty")
        if not self.sample_ids:
            raise ValueError("run manifest must contain at least one sample")


@dataclass(frozen=True, slots=True)
class EvaluationSampleResult:
    sample_id: str
    succeeded: bool
    scores: tuple[Score, ...] = ()
    error_code: str | None = None
    metrics: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    manifest: EvaluationRunManifest
    results: tuple[EvaluationSampleResult, ...]

    @property
    def complete(self) -> bool:
        expected = set(self.manifest.sample_ids)
        actual = {result.sample_id for result in self.results}
        return len(actual) == len(self.results) and actual == expected


def build_run_manifest(
    *,
    run_id: str,
    test_set: TestSet,
    selection: SampleSelection,
    model: str,
    runtime_fingerprint: str | None = None,
) -> EvaluationRunManifest:
    selected = selection.select(test_set)
    return EvaluationRunManifest(
        run_id=run_id,
        test_set_id=test_set.test_set_id,
        test_set_version=test_set.version,
        test_set_identity=test_set.identity,
        sample_ids=tuple(sample.sample_id for sample in selected),
        model=model,
        task_types=tuple(sorted({sample.task for sample in selected}, key=lambda task: task.value)),
        seed=selection.seed,
        runtime_fingerprint=runtime_fingerprint,
    )
