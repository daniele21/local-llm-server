from __future__ import annotations

from collections import deque

from local_llm_server.reclamation_evidence import RecoveryObservation
from local_llm_server.reclamation_experiment import (
    LifecycleErrorStage,
    run_reclamation_cycle,
    run_reclamation_experiment,
)
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _snapshot(*, available: int, rss: int, clock: float) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=clock,
        platform="test",
        total_memory_bytes=_measured(2_000),
        available_memory_bytes=_measured(available),
        process_rss_bytes=_measured(rss),
    )


class _Observer:
    def __init__(self, snapshots: list[SystemResourceSnapshot]) -> None:
        self.snapshots = deque(snapshots)

    def snapshot(self) -> SystemResourceSnapshot:
        return self.snapshots.popleft()


def test_reclamation_cycle_captures_full_window_without_promoting_pass():
    observer = _Observer([
        _snapshot(available=1_500, rss=100, clock=1),
        _snapshot(available=1_100, rss=420, clock=2),
        _snapshot(available=1_000, rss=520, clock=3),
        _snapshot(available=1_430, rss=130, clock=4),
    ])
    events: list[str] = []

    result = run_reclamation_cycle(
        observer,
        start=lambda: events.append("start") or object(),
        wait_ready=lambda runtime: events.append("ready"),
        exercise=lambda runtime: events.append("exercise"),
        stop=lambda runtime: events.append("stop"),
        cycle_index=7,
    )

    assert events == ["start", "ready", "exercise", "stop"]
    assert result.cycle_index == 7
    assert result.completed_without_error is True
    assert result.evidence.complete_window is True
    assert result.evidence.observation is RecoveryObservation.RECOVERY_OBSERVED
    public = result.to_public_dict()
    assert "pass" not in public
    assert "passed" not in public


def test_exercise_failure_still_stops_and_captures_after_stop():
    observer = _Observer([
        _snapshot(available=1_500, rss=100, clock=1),
        _snapshot(available=1_100, rss=420, clock=2),
        _snapshot(available=1_450, rss=120, clock=3),
    ])
    stopped: list[object] = []

    def exercise(runtime: object) -> None:
        raise RuntimeError("private backend details")

    result = run_reclamation_cycle(
        observer,
        start=object,
        wait_ready=lambda runtime: None,
        exercise=exercise,
        stop=lambda runtime: stopped.append(runtime),
    )

    assert len(stopped) == 1
    assert result.error_stage is LifecycleErrorStage.EXERCISE
    assert result.error_type == "RuntimeError"
    assert result.evidence.complete_window is True
    assert "private backend details" not in str(result.to_public_dict())


def test_start_failure_preserves_partial_evidence_and_stays_inconclusive():
    observer = _Observer([
        _snapshot(available=1_500, rss=100, clock=1),
        _snapshot(available=1_490, rss=105, clock=2),
    ])

    def fail_start() -> object:
        raise ValueError("failed to start")

    result = run_reclamation_cycle(
        observer,
        start=fail_start,
        wait_ready=lambda runtime: None,
        exercise=lambda runtime: None,
        stop=lambda runtime: None,
    )

    assert result.error_stage is LifecycleErrorStage.START
    assert result.evidence.complete_window is False
    assert result.evidence.observation is RecoveryObservation.INCONCLUSIVE


def test_repeated_experiment_reports_observation_counts_not_verdicts():
    observer = _Observer([
        _snapshot(available=1_500, rss=100, clock=1),
        _snapshot(available=1_100, rss=400, clock=2),
        _snapshot(available=1_000, rss=500, clock=3),
        _snapshot(available=1_450, rss=120, clock=4),
        _snapshot(available=1_500, rss=100, clock=5),
        _snapshot(available=1_100, rss=400, clock=6),
        _snapshot(available=1_000, rss=500, clock=7),
        _snapshot(available=1_050, rss=410, clock=8),
    ])

    report = run_reclamation_experiment(
        observer,
        cycles=2,
        start=object,
        wait_ready=lambda runtime: None,
        exercise=lambda runtime: None,
        stop=lambda runtime: None,
    )
    public = report.to_public_dict()

    assert public["cycle_count"] == 2
    assert public["complete_windows"] == 2
    assert public["observations"]["recovery_observed"] == 1
    assert public["observations"]["no_recovery_observed"] == 1
    assert "PASS/FAIL" in public["interpretation"]
    assert "pass" not in public
    assert "passed" not in public


def test_repeated_experiment_requires_positive_cycle_count():
    observer = _Observer([])

    try:
        run_reclamation_experiment(
            observer,
            cycles=0,
            start=object,
            wait_ready=lambda runtime: None,
            exercise=lambda runtime: None,
            stop=lambda runtime: None,
        )
    except ValueError as exc:
        assert str(exc) == "cycles must be >= 1"
    else:
        raise AssertionError("expected ValueError")
