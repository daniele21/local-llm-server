"""Bounded fair cross-runtime execution admission.

The governor owns only aggregate control-plane execution slots. Per-runtime FIFO
queues/semaphores and backend-native batching remain separate owners. Waiting is
bounded, runtime-fair, deadline-aware and privacy-safe; no request content is
retained or exposed.
"""
from __future__ import annotations

import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .core.contracts import ErrorCode, InferenceError


class GlobalExecutionState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(slots=True)
class _Waiter:
    request_id: str
    runtime_key: str
    submitted_at: float
    deadline_at: float | None
    state: GlobalExecutionState = GlobalExecutionState.QUEUED
    started_at: float | None = None
    finished_at: float | None = None

    def expired(self, now: float) -> bool:
        return self.deadline_at is not None and now >= self.deadline_at


@dataclass(frozen=True, slots=True)
class GlobalExecutionPermit:
    request_id: str
    runtime_key: str
    submitted_at: float
    started_at: float
    deadline_at: float | None

    @property
    def wait_ms(self) -> float:
        return max(0.0, (self.started_at - self.submitted_at) * 1000.0)


@dataclass(frozen=True, slots=True)
class GlobalExecutionSnapshot:
    max_running: int
    queue_capacity: int
    inflight: int
    queued: int
    runtimes: tuple[dict[str, object], ...]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "enabled": True,
            "max_running": self.max_running,
            "queue_capacity": self.queue_capacity,
            "inflight": self.inflight,
            "queued": self.queued,
            "fairness": "runtime_round_robin",
            "runtimes": [dict(item) for item in self.runtimes],
        }


class GlobalExecutionGovernor:
    """Bound aggregate running work with round-robin fairness by runtime."""

    def __init__(
        self,
        *,
        max_running: int,
        queue_capacity: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_running < 1:
            raise ValueError("max_running must be >= 1")
        if queue_capacity < 1:
            raise ValueError("queue_capacity must be >= 1")
        self.max_running = max_running
        self.queue_capacity = queue_capacity
        self.clock = clock
        self._condition = threading.Condition(threading.RLock())
        self._waiters: dict[str, _Waiter] = {}
        self._runtime_queues: dict[str, deque[str]] = {}
        self._runtime_order: deque[str] = deque()
        self._runtime_in_order: set[str] = set()
        self._inflight = 0

    def acquire(
        self,
        runtime_key: str,
        request_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> GlobalExecutionPermit:
        if not runtime_key.strip():
            raise ValueError("runtime_key must be non-empty")
        if not request_id.strip():
            raise ValueError("request_id must be non-empty")
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise InferenceError(
                ErrorCode.TIMEOUT,
                "request deadline expired while waiting for global execution admission",
                retryable=True,
                details={},
            )

        now = self.clock()
        with self._condition:
            if request_id in self._waiters:
                raise ValueError(f"request_id already exists: {request_id}")
            self._expire_queued_locked(now)
            self._admit_available_locked(now)
            queued = sum(
                1
                for item in self._waiters.values()
                if item.state is GlobalExecutionState.QUEUED
            )
            if self._inflight >= self.max_running and queued >= self.queue_capacity:
                raise InferenceError(
                    ErrorCode.RESOURCE_EXHAUSTED,
                    "global execution queue is full",
                    retryable=True,
                    details={"capacity": self.queue_capacity},
                )

            waiter = _Waiter(
                request_id=request_id,
                runtime_key=runtime_key,
                submitted_at=now,
                deadline_at=(now + timeout_seconds) if timeout_seconds is not None else None,
            )
            self._waiters[request_id] = waiter
            self._runtime_queues.setdefault(runtime_key, deque()).append(request_id)
            self._schedule_runtime_locked(runtime_key)
            self._admit_available_locked(now)
            self._condition.notify_all()

            while True:
                if waiter.state is GlobalExecutionState.RUNNING:
                    assert waiter.started_at is not None
                    return GlobalExecutionPermit(
                        request_id=waiter.request_id,
                        runtime_key=waiter.runtime_key,
                        submitted_at=waiter.submitted_at,
                        started_at=waiter.started_at,
                        deadline_at=waiter.deadline_at,
                    )
                if waiter.state is GlobalExecutionState.EXPIRED:
                    self._waiters.pop(request_id, None)
                    raise InferenceError(
                        ErrorCode.TIMEOUT,
                        "request deadline expired while waiting for global execution admission",
                        retryable=True,
                        details={},
                    )
                if waiter.state is GlobalExecutionState.CANCELLED:
                    self._waiters.pop(request_id, None)
                    raise InferenceError(
                        ErrorCode.CANCELLED,
                        "request was cancelled before global execution admission",
                        retryable=False,
                        details={},
                    )

                now = self.clock()
                self._expire_queued_locked(now)
                self._admit_available_locked(now)
                if waiter.state is not GlobalExecutionState.QUEUED:
                    continue
                remaining = (
                    None
                    if waiter.deadline_at is None
                    else max(0.0, waiter.deadline_at - now)
                )
                if remaining is not None and remaining <= 0:
                    continue
                self._condition.wait(timeout=remaining)

    def abandon(self, request_id: str) -> bool:
        """Cancel a permit acquisition that will not be handed to execution."""
        now = self.clock()
        with self._condition:
            waiter = self._waiters.get(request_id)
            if waiter is None:
                return False
            if waiter.state is GlobalExecutionState.QUEUED:
                waiter.state = GlobalExecutionState.CANCELLED
                waiter.finished_at = now
            elif waiter.state is GlobalExecutionState.RUNNING:
                waiter.state = GlobalExecutionState.CANCELLED
                waiter.finished_at = now
                self._inflight = max(0, self._inflight - 1)
            else:
                return False
            self._waiters.pop(request_id, None)
            self._admit_available_locked(now)
            self._condition.notify_all()
            return True

    def release(self, request_id: str) -> None:
        now = self.clock()
        with self._condition:
            waiter = self._waiters.get(request_id)
            if waiter is None:
                raise KeyError(request_id)
            if waiter.state is not GlobalExecutionState.RUNNING:
                raise RuntimeError(
                    f"request {request_id} cannot release from {waiter.state.value}"
                )
            waiter.state = GlobalExecutionState.COMPLETED
            waiter.finished_at = now
            self._inflight = max(0, self._inflight - 1)
            self._waiters.pop(request_id, None)
            self._admit_available_locked(now)
            self._condition.notify_all()

    def snapshot(self) -> GlobalExecutionSnapshot:
        now = self.clock()
        with self._condition:
            self._expire_queued_locked(now)
            self._admit_available_locked(now)
            queued_by_runtime: Counter[str] = Counter()
            running_by_runtime: Counter[str] = Counter()
            for waiter in self._waiters.values():
                if waiter.state is GlobalExecutionState.QUEUED:
                    queued_by_runtime[waiter.runtime_key] += 1
                elif waiter.state is GlobalExecutionState.RUNNING:
                    running_by_runtime[waiter.runtime_key] += 1
            runtime_keys = sorted(set(queued_by_runtime) | set(running_by_runtime))
            runtimes = tuple(
                {
                    "runtime_key": runtime_key,
                    "queued": queued_by_runtime[runtime_key],
                    "running": running_by_runtime[runtime_key],
                }
                for runtime_key in runtime_keys
            )
            return GlobalExecutionSnapshot(
                max_running=self.max_running,
                queue_capacity=self.queue_capacity,
                inflight=self._inflight,
                queued=sum(queued_by_runtime.values()),
                runtimes=runtimes,
            )

    def _schedule_runtime_locked(self, runtime_key: str) -> None:
        if runtime_key in self._runtime_in_order:
            return
        queue = self._runtime_queues.get(runtime_key)
        if not queue:
            return
        self._runtime_order.append(runtime_key)
        self._runtime_in_order.add(runtime_key)

    def _admit_available_locked(self, now: float) -> None:
        while self._inflight < self.max_running and self._runtime_order:
            runtime_key = self._runtime_order.popleft()
            self._runtime_in_order.discard(runtime_key)
            queue = self._runtime_queues.get(runtime_key)
            if queue is None:
                continue

            selected: _Waiter | None = None
            while queue:
                request_id = queue.popleft()
                waiter = self._waiters.get(request_id)
                if waiter is None or waiter.state is not GlobalExecutionState.QUEUED:
                    continue
                if waiter.expired(now):
                    waiter.state = GlobalExecutionState.EXPIRED
                    waiter.finished_at = now
                    continue
                selected = waiter
                break

            if queue:
                self._schedule_runtime_locked(runtime_key)
            else:
                self._runtime_queues.pop(runtime_key, None)

            if selected is None:
                continue
            selected.state = GlobalExecutionState.RUNNING
            selected.started_at = now
            self._inflight += 1

    def _expire_queued_locked(self, now: float) -> None:
        changed = False
        for waiter in self._waiters.values():
            if waiter.state is GlobalExecutionState.QUEUED and waiter.expired(now):
                waiter.state = GlobalExecutionState.EXPIRED
                waiter.finished_at = now
                changed = True
        if changed:
            self._condition.notify_all()
