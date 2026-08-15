from __future__ import annotations

import pytest

from local_llm_server.resources import ResourceValue, ResourceValueSource, SystemResourceSnapshot
from local_llm_server.worker_protocol import (
    WorkerCommand,
    WorkerLifecycle,
    WorkerResourceEvidence,
    WorkerState,
)


def _snapshot(memory: int) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=float(memory),
        platform="test",
        total_memory_bytes=ResourceValue(1000, ResourceValueSource.MEASURED, "bytes"),
        available_memory_bytes=ResourceValue(memory, ResourceValueSource.MEASURED, "bytes"),
    )


def test_worker_lifecycle_happy_path():
    lifecycle = WorkerLifecycle()

    assert lifecycle.accepts(WorkerCommand.START) is True
    lifecycle.transition(WorkerState.STARTING)
    lifecycle.transition(WorkerState.READY)
    assert lifecycle.accepts(WorkerCommand.GENERATE) is True
    lifecycle.transition(WorkerState.DRAINING)
    assert lifecycle.accepts(WorkerCommand.GENERATE) is False
    assert lifecycle.accepts(WorkerCommand.CANCEL) is True
    lifecycle.transition(WorkerState.STOPPING)
    lifecycle.transition(WorkerState.STOPPED)
    assert lifecycle.accepts(WorkerCommand.HEALTH) is False


def test_invalid_transition_is_rejected():
    lifecycle = WorkerLifecycle()

    with pytest.raises(ValueError, match="invalid worker transition"):
        lifecycle.transition(WorkerState.READY)


def test_terminal_stopped_state_is_idempotent_but_not_restartable():
    lifecycle = WorkerLifecycle()
    lifecycle.transition(WorkerState.STOPPED)

    assert lifecycle.transition(WorkerState.STOPPED) is WorkerState.STOPPED
    assert lifecycle.accepts(WorkerCommand.START) is False
    assert lifecycle.accepts(WorkerCommand.STOP) is False


def test_failed_worker_can_still_move_to_cleanup():
    lifecycle = WorkerLifecycle()
    lifecycle.transition(WorkerState.FAILED)
    lifecycle.transition(WorkerState.STOPPING)
    lifecycle.transition(WorkerState.STOPPED)

    assert lifecycle.state is WorkerState.STOPPED


def test_resource_evidence_requires_ready_and_stopped_snapshots_for_window():
    incomplete = WorkerResourceEvidence(after_ready=_snapshot(500))
    complete = WorkerResourceEvidence(after_ready=_snapshot(500), after_stop=_snapshot(900))

    assert incomplete.has_reclamation_window is False
    assert complete.has_reclamation_window is True
