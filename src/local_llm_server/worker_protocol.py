"""Pure worker lifecycle protocol for reclaimable runtime isolation.

This module defines commands, states and evidence hooks only. It does not claim
that a subprocess worker implementation exists yet; later B3 slices bind these
contracts to managed processes and representative memory evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .resources import SystemResourceSnapshot


class WorkerState(str, Enum):
    NEW = "new"
    STARTING = "starting"
    READY = "ready"
    DRAINING = "draining"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class WorkerCommand(str, Enum):
    START = "start"
    PREPARE = "prepare"
    GENERATE = "generate"
    CANCEL = "cancel"
    DRAIN = "drain"
    STOP = "stop"
    HEALTH = "health"


@dataclass(frozen=True, slots=True)
class WorkerRequest:
    request_id: str
    command: WorkerCommand
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must be non-empty")


@dataclass(frozen=True, slots=True)
class WorkerResponse:
    request_id: str
    accepted: bool
    state: WorkerState
    error_code: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkerResourceEvidence:
    before_start: SystemResourceSnapshot | None = None
    after_ready: SystemResourceSnapshot | None = None
    peak: SystemResourceSnapshot | None = None
    after_stop: SystemResourceSnapshot | None = None

    @property
    def has_reclamation_window(self) -> bool:
        return self.after_ready is not None and self.after_stop is not None


class WorkerLifecycle:
    """Deterministic state machine shared by future worker implementations."""

    _TRANSITIONS: dict[WorkerState, frozenset[WorkerState]] = {
        WorkerState.NEW: frozenset({WorkerState.STARTING, WorkerState.STOPPED, WorkerState.FAILED}),
        WorkerState.STARTING: frozenset({WorkerState.READY, WorkerState.STOPPING, WorkerState.FAILED}),
        WorkerState.READY: frozenset({WorkerState.DRAINING, WorkerState.STOPPING, WorkerState.FAILED}),
        WorkerState.DRAINING: frozenset({WorkerState.READY, WorkerState.STOPPING, WorkerState.FAILED}),
        WorkerState.STOPPING: frozenset({WorkerState.STOPPED, WorkerState.FAILED}),
        WorkerState.STOPPED: frozenset(),
        WorkerState.FAILED: frozenset({WorkerState.STOPPING, WorkerState.STOPPED}),
    }

    def __init__(self) -> None:
        self._state = WorkerState.NEW

    @property
    def state(self) -> WorkerState:
        return self._state

    def transition(self, target: WorkerState) -> WorkerState:
        if target == self._state:
            return self._state
        if target not in self._TRANSITIONS[self._state]:
            raise ValueError(f"invalid worker transition: {self._state.value} -> {target.value}")
        self._state = target
        return self._state

    def accepts(self, command: WorkerCommand) -> bool:
        if command is WorkerCommand.HEALTH:
            return self._state not in {WorkerState.STOPPED}
        if command is WorkerCommand.START:
            return self._state is WorkerState.NEW
        if command in {WorkerCommand.PREPARE, WorkerCommand.GENERATE}:
            return self._state is WorkerState.READY
        if command is WorkerCommand.CANCEL:
            return self._state in {WorkerState.READY, WorkerState.DRAINING}
        if command is WorkerCommand.DRAIN:
            return self._state is WorkerState.READY
        if command is WorkerCommand.STOP:
            return self._state not in {WorkerState.STOPPED, WorkerState.STOPPING}
        return False
