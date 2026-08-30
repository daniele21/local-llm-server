"""Shared transient resource reservation primitive for active inference work."""
from __future__ import annotations

from dataclasses import dataclass

from .memory_envelope import MemoryEnvelope
from .resource_manager import (
    AdmissionDecision,
    AdmissionResult,
    ReservationKind,
    ResourceManager,
)


@dataclass(slots=True)
class TransientResourceReservation:
    """One active transient ledger owner that releases idempotently."""

    manager: ResourceManager
    reservation_id: str
    envelope: MemoryEnvelope
    result: AdmissionResult
    active: bool = True

    def release(self) -> bool:
        if not self.active:
            return False
        self.active = False
        return self.manager.release(self.reservation_id)


def reserve_transient_resource(
    resource_manager: ResourceManager | None,
    *,
    reservation_id: str,
    envelope: MemoryEnvelope,
) -> tuple[AdmissionResult | None, TransientResourceReservation | None]:
    """Reserve and commit one transient estimate in the global ledger.

    ``None`` result means no manager or no accountable estimate. An unbounded
    configured manager returns ``UNKNOWN`` without creating a false owner. A
    rejected commit is rolled back before returning.
    """
    estimate_bytes = envelope.accounted_bytes
    if resource_manager is None or estimate_bytes is None:
        return None, None

    result = resource_manager.reserve(
        reservation_id,
        estimate_bytes,
        kind=ReservationKind.TRANSIENT,
    )
    if result.decision is not AdmissionDecision.ADMIT:
        return result, None

    committed = resource_manager.commit(reservation_id)
    if committed.decision is AdmissionDecision.REJECT:
        resource_manager.release(reservation_id)
        return committed, None
    if committed.decision is AdmissionDecision.UNKNOWN:
        # Defensive only: an UNKNOWN reserve does not create an owner today.
        resource_manager.release(reservation_id)
        return committed, None

    return committed, TransientResourceReservation(
        manager=resource_manager,
        reservation_id=reservation_id,
        envelope=envelope,
        result=committed,
    )
