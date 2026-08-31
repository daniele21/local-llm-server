"""Resource reservation and admission foundation.

This module manages configured budget accounting only. It does not claim that a
runtime can reclaim memory; representative-device evidence owns reclamation.
Resident runtimes and active requests share one ledger so individually safe
owners cannot collectively exceed the configured usable budget.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum

from .resources import ResourceBudget


class AdmissionDecision(str, Enum):
    ADMIT = "admit"
    REJECT = "reject"
    UNKNOWN = "unknown"


class ReservationState(str, Enum):
    RESERVED = "reserved"
    COMMITTED = "committed"


class ReservationKind(str, Enum):
    RESIDENT = "resident"
    TRANSIENT = "transient"


@dataclass(frozen=True, slots=True)
class ResourceReservation:
    reservation_id: str
    requested_bytes: int
    accounted_bytes: int
    state: ReservationState
    kind: ReservationKind = ReservationKind.RESIDENT


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    decision: AdmissionDecision
    requested_bytes: int
    committed_bytes: int
    reserved_bytes: int
    usable_budget_bytes: int | None
    reason: str


class ResourceManager:
    """Thread-safe configured-budget ledger shared by all memory owners."""

    def __init__(self, budget: ResourceBudget) -> None:
        self._budget = budget
        self._reservations: dict[str, ResourceReservation] = {}
        self._lock = threading.RLock()

    @property
    def budget(self) -> ResourceBudget:
        return self._budget

    def snapshot(
        self,
        *,
        kind: ReservationKind | None = None,
    ) -> tuple[ResourceReservation, ...]:
        with self._lock:
            reservations = self._reservations.values()
            if kind is not None:
                reservations = (item for item in reservations if item.kind is kind)
            return tuple(sorted(reservations, key=lambda item: item.reservation_id))

    def reserve(
        self,
        reservation_id: str,
        requested_bytes: int,
        *,
        kind: ReservationKind = ReservationKind.RESIDENT,
    ) -> AdmissionResult:
        if not reservation_id.strip():
            raise ValueError("reservation_id must be non-empty")
        if requested_bytes < 0:
            raise ValueError("requested_bytes must be >= 0")

        with self._lock:
            if reservation_id in self._reservations:
                raise ValueError(f"reservation already exists: {reservation_id}")
            decision = self._decision_for(requested_bytes)
            if decision.decision is AdmissionDecision.ADMIT:
                self._reservations[reservation_id] = ResourceReservation(
                    reservation_id=reservation_id,
                    requested_bytes=requested_bytes,
                    accounted_bytes=requested_bytes,
                    state=ReservationState.RESERVED,
                    kind=kind,
                )
            return decision

    def commit(self, reservation_id: str, *, observed_bytes: int | None = None) -> AdmissionResult:
        if observed_bytes is not None and observed_bytes < 0:
            raise ValueError("observed_bytes must be >= 0")
        with self._lock:
            current = self._require(reservation_id)
            accounted = current.accounted_bytes if observed_bytes is None else observed_bytes
            other_bytes = sum(
                item.accounted_bytes
                for key, item in self._reservations.items()
                if key != reservation_id
            )
            usable = self._budget.usable_bytes
            if usable is not None and other_bytes + accounted > usable:
                return self._result(
                    AdmissionDecision.REJECT,
                    requested_bytes=accounted,
                    reason="observed footprint exceeds configured usable budget",
                )
            self._reservations[reservation_id] = ResourceReservation(
                reservation_id=reservation_id,
                requested_bytes=current.requested_bytes,
                accounted_bytes=accounted,
                state=ReservationState.COMMITTED,
                kind=current.kind,
            )
            return self._result(
                AdmissionDecision.ADMIT if usable is not None else AdmissionDecision.UNKNOWN,
                requested_bytes=accounted,
                reason=(
                    "committed within configured budget"
                    if usable is not None
                    else "no configured resource limit; accounting recorded without enforceable admission"
                ),
            )

    def release(self, reservation_id: str) -> bool:
        with self._lock:
            return self._reservations.pop(reservation_id, None) is not None

    def rollback(self, reservation_id: str) -> bool:
        return self.release(reservation_id)

    def _decision_for(self, requested_bytes: int) -> AdmissionResult:
        usable = self._budget.usable_bytes
        if usable is None:
            return self._result(
                AdmissionDecision.UNKNOWN,
                requested_bytes=requested_bytes,
                reason="no configured resource limit",
            )
        accounted = sum(item.accounted_bytes for item in self._reservations.values())
        if accounted + requested_bytes > usable:
            return self._result(
                AdmissionDecision.REJECT,
                requested_bytes=requested_bytes,
                reason="configured usable budget would be exceeded",
            )
        return self._result(
            AdmissionDecision.ADMIT,
            requested_bytes=requested_bytes,
            reason="reservation fits configured usable budget",
        )

    def _result(
        self,
        decision: AdmissionDecision,
        *,
        requested_bytes: int,
        reason: str,
    ) -> AdmissionResult:
        committed = sum(
            item.accounted_bytes
            for item in self._reservations.values()
            if item.state is ReservationState.COMMITTED
        )
        reserved = sum(
            item.accounted_bytes
            for item in self._reservations.values()
            if item.state is ReservationState.RESERVED
        )
        return AdmissionResult(
            decision=decision,
            requested_bytes=requested_bytes,
            committed_bytes=committed,
            reserved_bytes=reserved,
            usable_budget_bytes=self._budget.usable_bytes,
            reason=reason,
        )

    def _require(self, reservation_id: str) -> ResourceReservation:
        try:
            return self._reservations[reservation_id]
        except KeyError as exc:
            raise KeyError(f"unknown reservation: {reservation_id}") from exc
