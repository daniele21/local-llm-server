from __future__ import annotations

from fastapi.testclient import TestClient

from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.residency_api import install_residency_api
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _cfg(key: str) -> dict:
    return {
        "model": key,
        "model_id": f"org/{key}",
        "backend": "fake",
        "modalities": ["text"],
        "max_concurrent_requests": 1,
    }


def _manager() -> ProductRuntimeManager:
    manager = ProductRuntimeManager(default_model="a")
    manager.add(_cfg("a"), _Engine(), key="a")
    manager.add(_cfg("b"), _Engine(), key="b")
    return manager


def test_runtime_pin_controls_only_automatic_eviction_eligibility():
    manager = _manager()

    before = manager.residency_policy_snapshot()
    a_before = next(item for item in before["runtimes"] if item["key"] == "a")
    assert a_before["pinned"] is False
    assert a_before["evictable"] is True

    manager.set_pinned("a", True)
    pinned = manager.residency_policy_snapshot()
    a_pinned = next(item for item in pinned["runtimes"] if item["key"] == "a")
    assert a_pinned["pinned"] is True
    assert a_pinned["evictable"] is False

    manager.set_pinned("a", False)
    unpinned = manager.residency_policy_snapshot()
    a_unpinned = next(item for item in unpinned["runtimes"] if item["key"] == "a")
    assert a_unpinned["evictable"] is True


def test_active_runtime_is_never_reported_evictable():
    manager = _manager()
    runtime = manager.resolve("a")

    with manager.lease_runtime(runtime):
        snapshot = manager.residency_policy_snapshot()
        current = next(item for item in snapshot["runtimes"] if item["key"] == "a")
        assert current["active_requests"] == 1
        assert current["evictable"] is False

    after = manager.residency_policy_snapshot()
    current = next(item for item in after["runtimes"] if item["key"] == "a")
    assert current["active_requests"] == 0
    assert current["evictable"] is True


def test_manual_unload_of_pinned_runtime_remains_explicitly_allowed():
    manager = _manager()
    manager.set_pinned("b", True)
    engine = manager.resolve("b").engine

    stopped = manager.unload("b")

    assert stopped.key == "b"
    assert engine.closed is True
    assert all(item["key"] != "b" for item in manager.residency_policy_snapshot()["runtimes"])


def test_residency_api_is_admin_only_and_mutates_pin_state():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_residency_api(app)
    client = TestClient(app)

    initial = client.get("/api/v1/residency")
    assert initial.status_code == 200
    assert initial.json()["supported"] is True

    updated = client.post(
        "/api/v1/residency/pin",
        json={"model": "a", "pinned": True},
    )
    assert updated.status_code == 200
    assert updated.json()["pinned"] is True
    runtime = next(item for item in updated.json()["residency"]["runtimes"] if item["key"] == "a")
    assert runtime["pinned"] is True
    assert runtime["evictable"] is False


def test_residency_api_is_absent_when_admin_api_is_disabled():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=False))
    install_residency_api(app)

    assert TestClient(app).get("/api/v1/residency").status_code == 404
