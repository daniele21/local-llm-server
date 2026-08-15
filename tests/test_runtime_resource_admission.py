from __future__ import annotations

from pathlib import Path

import pytest

from local_llm_server.resource_manager import ReservationState, ResourceManager
from local_llm_server.resources import ResourceBudget
from local_llm_server.runtime import (
    ModelRuntimeManager,
    ResourceAdmissionError,
)
from local_llm_server.runtime_admission import estimated_runtime_load_bytes


class _Engine:
    backend = "fake"

    def __init__(self):
        self.stopped = False

    def shutdown(self):
        self.stopped = True


def _cfg(key: str, estimate: int, *, model_id: str | None = None) -> dict:
    return {
        "model": key,
        "model_id": model_id or key,
        "backend": "fake",
        "model_path": f"/models/{key}",
        "resource_estimate_bytes": estimate,
    }


def test_explicit_estimate_precedes_registry_size_and_file_size(tmp_path: Path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"1234567890")
    cfg = {
        "resource_estimate_bytes": 7,
        "size_gb": 5,
        "model_path": str(artifact),
    }
    assert estimated_runtime_load_bytes(cfg) == 7


def test_local_file_size_is_fallback_estimate(tmp_path: Path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"1234567890")
    assert estimated_runtime_load_bytes({"model_path": str(artifact)}) == 10


def test_rejected_load_never_invokes_backend(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=100, headroom_bytes=10))
    manager = ModelRuntimeManager(resource_manager=resources)
    called = []

    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("too-big", 91),
    )
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: called.append(cfg) or _Engine(),
    )

    with pytest.raises(ResourceAdmissionError) as exc_info:
        manager.load("too-big")

    assert exc_info.value.result.decision.value == "reject"
    assert called == []
    assert resources.snapshot() == ()
    assert manager.list() == []


def test_successful_load_commits_reservation_and_exposes_status_metadata(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=1_000))
    manager = ModelRuntimeManager(resource_manager=resources)
    engine = _Engine()

    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("model", 400),
    )
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda _cfg: engine)

    runtime, loaded = manager.load("model")

    assert loaded is True
    [reservation] = resources.snapshot()
    assert reservation.state is ReservationState.COMMITTED
    assert reservation.accounted_bytes == 400
    assert runtime.resource_reservation_id == reservation.reservation_id
    status = runtime.snapshot_status()
    assert status["resource_admission"]["decision"] == "admit"
    assert status["resource_admission"]["estimate_bytes"] == 400


def test_backend_load_failure_rolls_back_reservation(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=1_000))
    manager = ModelRuntimeManager(resource_manager=resources)

    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("broken", 400),
    )

    def fail_load(_cfg):
        raise RuntimeError("backend failed")

    monkeypatch.setattr("local_llm_server.engine.load_llm", fail_load)

    with pytest.raises(RuntimeError, match="backend failed"):
        manager.load("broken")

    assert resources.snapshot() == ()
    assert manager.list() == []


def test_unload_releases_committed_accounting(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=2_000))
    manager = ModelRuntimeManager(resource_manager=resources)
    manager.add(
        {"model": "anchor", "model_id": "anchor", "backend": "fake"},
        _Engine(),
    )

    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("managed", 500),
    )
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda _cfg: _Engine())

    runtime, _ = manager.load("managed")
    assert runtime.resource_reservation_id is not None
    assert len(resources.snapshot()) == 1

    manager.unload("managed")
    assert resources.snapshot() == ()
    assert runtime.engine.stopped is True


def test_reload_rejects_peak_overlap_and_preserves_existing_runtime(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=1_000))
    manager = ModelRuntimeManager(default_model="model", resource_manager=resources)

    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("model", 600),
    )
    first_engine = _Engine()
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda _cfg: first_engine)
    current, _ = manager.load("model")
    assert len(resources.snapshot()) == 1

    second_load_called = []
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: second_load_called.append(cfg) or _Engine(),
    )

    with pytest.raises(ResourceAdmissionError):
        manager.reload("model")

    # 600 old + 600 replacement would exceed the 1000 budget, so rejection
    # happens before invoking the expensive replacement backend load.
    assert second_load_called == []
    assert manager.resolve("model") is current
    assert current.state.value == "ready"
    assert current.engine is first_engine
    assert first_engine.stopped is False
    [reservation] = resources.snapshot()
    assert reservation.accounted_bytes == 600
    assert reservation.state is ReservationState.COMMITTED


def test_no_configured_budget_stays_unknown_without_false_reservation(monkeypatch):
    resources = ResourceManager(ResourceBudget(limit_bytes=None))
    manager = ModelRuntimeManager(resource_manager=resources)
    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: _cfg("unbounded", 500),
    )
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda _cfg: _Engine())

    runtime, _ = manager.load("unbounded")

    assert runtime.resource_reservation_id is None
    assert resources.snapshot() == ()
    assert runtime.snapshot_status()["resource_admission"]["decision"] == "unknown"
