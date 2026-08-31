from __future__ import annotations

from local_llm_server.resource_manager import (
    AdmissionDecision,
    ReservationKind,
    ReservationState,
    ResourceManager,
)
from local_llm_server.resources import ResourceBudget


def test_resident_and_transient_reservations_share_one_budget():
    manager = ResourceManager(ResourceBudget(limit_bytes=100))
    resident = manager.reserve("runtime:model", 70, kind=ReservationKind.RESIDENT)
    assert resident.decision is AdmissionDecision.ADMIT
    manager.commit("runtime:model")

    transient = manager.reserve("request:model:one", 40, kind=ReservationKind.TRANSIENT)

    assert transient.decision is AdmissionDecision.REJECT
    [reservation] = manager.snapshot()
    assert reservation.kind is ReservationKind.RESIDENT
    assert reservation.accounted_bytes == 70


def test_kind_survives_commit_and_snapshot_can_filter():
    manager = ResourceManager(ResourceBudget(limit_bytes=100))
    manager.reserve("runtime:model", 20, kind=ReservationKind.RESIDENT)
    manager.commit("runtime:model")
    manager.reserve("request:model:one", 30, kind=ReservationKind.TRANSIENT)
    manager.commit("request:model:one")

    [resident] = manager.snapshot(kind=ReservationKind.RESIDENT)
    [transient] = manager.snapshot(kind=ReservationKind.TRANSIENT)

    assert resident.state is ReservationState.COMMITTED
    assert resident.kind is ReservationKind.RESIDENT
    assert transient.state is ReservationState.COMMITTED
    assert transient.kind is ReservationKind.TRANSIENT
