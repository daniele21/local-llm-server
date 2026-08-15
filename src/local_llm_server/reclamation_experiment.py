"""Repeatable lifecycle harness for host-resource reclamation evidence.

This module orchestrates evidence capture around real runtime/worker lifecycle
callbacks. It intentionally reports observations rather than a PASS/FAIL claim:
representative hardware, backend and repeated-cycle context remain necessary to
interpret memory recovery.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .reclamation_evidence import (
    EvidenceStage,
    ReclamationEvidence,
    ReclamationEvidenceRecorder,
    RecoveryObservation,
)
from .resources import ResourceObserver


class LifecycleErrorStage(str, Enum):
    START = "start"
    READY = "ready"
    EXERCISE = "exercise"
    STOP = "stop"
    SETTLE = "settle"


@dataclass(frozen=True, slots=True)
class ReclamationCycleResult:
    cycle_index: int
    evidence: ReclamationEvidence
    error_stage: LifecycleErrorStage | None = None
    error_type: str | None = None

    @property
    def completed_without_error(self) -> bool:
        return self.error_stage is None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "cycle_index": self.cycle_index,
            "evidence": self.evidence.to_public_dict(),
            "error_stage": self.error_stage.value if self.error_stage else None,
            "error_type": self.error_type,
            "completed_without_error": self.completed_without_error,
        }


@dataclass(frozen=True, slots=True)
class ReclamationExperimentReport:
    cycles: tuple[ReclamationCycleResult, ...]

    def to_public_dict(self) -> dict[str, object]:
        observations = {value.value: 0 for value in RecoveryObservation}
        complete_windows = 0
        errors = 0
        for cycle in self.cycles:
            observations[cycle.evidence.observation.value] += 1
            if cycle.evidence.complete_window:
                complete_windows += 1
            if cycle.error_stage is not None:
                errors += 1
        return {
            "cycle_count": len(self.cycles),
            "complete_windows": complete_windows,
            "error_cycles": errors,
            "observations": observations,
            "cycles": [cycle.to_public_dict() for cycle in self.cycles],
            "interpretation": (
                "Observational evidence only. This report does not declare "
                "memory reclamation or backend unload behavior PASS/FAIL."
            ),
        }


def run_reclamation_cycle(
    observer: ResourceObserver,
    *,
    start: Callable[[], Any],
    wait_ready: Callable[[Any], None],
    exercise: Callable[[Any], None],
    stop: Callable[[Any], None],
    settle_after_stop: Callable[[], None] | None = None,
    cycle_index: int = 0,
) -> ReclamationCycleResult:
    """Run one lifecycle window and capture every checkpoint that is reached.

    Cleanup is attempted whenever ``start`` returns a runtime handle, including
    when readiness or exercise fails. Errors are reduced to stage + exception
    type in the public result to avoid leaking backend paths/messages.
    """
    recorder = ReclamationEvidenceRecorder(observer)
    recorder.capture(EvidenceStage.BEFORE_START)

    runtime: Any = None
    error_stage: LifecycleErrorStage | None = None
    error_type: str | None = None

    try:
        runtime = start()
    except Exception as exc:  # lifecycle harness must preserve partial evidence
        error_stage = LifecycleErrorStage.START
        error_type = type(exc).__name__

    if runtime is not None and error_stage is None:
        try:
            wait_ready(runtime)
            recorder.capture(EvidenceStage.AFTER_READY)
        except Exception as exc:
            error_stage = LifecycleErrorStage.READY
            error_type = type(exc).__name__

    if runtime is not None and error_stage is None:
        try:
            exercise(runtime)
            recorder.capture(EvidenceStage.PEAK)
        except Exception as exc:
            error_stage = LifecycleErrorStage.EXERCISE
            error_type = type(exc).__name__

    if runtime is not None:
        try:
            stop(runtime)
        except Exception as exc:
            if error_stage is None:
                error_stage = LifecycleErrorStage.STOP
                error_type = type(exc).__name__

    if settle_after_stop is not None:
        try:
            settle_after_stop()
        except Exception as exc:
            if error_stage is None:
                error_stage = LifecycleErrorStage.SETTLE
                error_type = type(exc).__name__

    # Capture after the stop attempt even on failures. The evidence recorder
    # will remain inconclusive when the necessary measured endpoints are absent.
    recorder.capture(EvidenceStage.AFTER_STOP)

    return ReclamationCycleResult(
        cycle_index=cycle_index,
        evidence=recorder.build(),
        error_stage=error_stage,
        error_type=error_type,
    )


def run_reclamation_experiment(
    observer: ResourceObserver,
    *,
    cycles: int,
    start: Callable[[], Any],
    wait_ready: Callable[[Any], None],
    exercise: Callable[[Any], None],
    stop: Callable[[Any], None],
    settle_after_stop: Callable[[], None] | None = None,
) -> ReclamationExperimentReport:
    """Run repeated lifecycle windows using the same observer and callbacks."""
    if cycles < 1:
        raise ValueError("cycles must be >= 1")
    results = tuple(
        run_reclamation_cycle(
            observer,
            start=start,
            wait_ready=wait_ready,
            exercise=exercise,
            stop=stop,
            settle_after_stop=settle_after_stop,
            cycle_index=index,
        )
        for index in range(cycles)
    )
    return ReclamationExperimentReport(results)
