from __future__ import annotations

import gc
import tracemalloc

from local_llm_server.resource_manager import AdmissionDecision, ResourceManager
from local_llm_server.resources import ResourceBudget


def _complete_cycle(manager: ResourceManager, reservation_id: str = "cycle") -> None:
    admitted = manager.reserve(reservation_id, 1024)
    assert admitted.decision is AdmissionDecision.ADMIT
    committed = manager.commit(reservation_id, observed_bytes=1536)
    assert committed.decision is AdmissionDecision.ADMIT
    assert manager.release(reservation_id) is True


def test_repeated_resource_lifecycle_returns_to_empty_ledger() -> None:
    manager = ResourceManager(ResourceBudget(limit_bytes=1024 * 1024, headroom_bytes=4096))
    for _ in range(5000):
        _complete_cycle(manager)
    assert manager.snapshot() == ()


def test_rejected_admission_does_not_accumulate_state() -> None:
    manager = ResourceManager(ResourceBudget(limit_bytes=4096, headroom_bytes=1024))
    for index in range(5000):
        result = manager.reserve(f"reject-{index}", 4096)
        assert result.decision is AdmissionDecision.REJECT
    assert manager.snapshot() == ()


def test_resource_manager_python_heap_does_not_grow_with_completed_cycles() -> None:
    """Bound Python-owned ledger retention; this is not a native-memory claim."""
    manager = ResourceManager(ResourceBudget(limit_bytes=1024 * 1024, headroom_bytes=4096))
    tracemalloc.start()
    try:
        for _ in range(1000):
            _complete_cycle(manager)
        gc.collect()
        baseline_current, _ = tracemalloc.get_traced_memory()

        for _ in range(10000):
            _complete_cycle(manager)
        gc.collect()
        measured_current, _ = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    retained_growth = max(0, measured_current - baseline_current)
    assert manager.snapshot() == ()
    assert retained_growth <= 524288
