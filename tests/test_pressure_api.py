from __future__ import annotations

from collections import deque

from fastapi.testclient import TestClient

from local_llm_server.pressure_api import install_pressure_dry_run_api
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.residency_pressure import PressureEvictionPolicy
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)
from local_llm_server.server import ServerSettings, create_app


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _snapshot(*, available: int | None) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=1.0,
        platform="test",
        total_memory_bytes=(
            _measured(1_000)
            if available is not None
            else ResourceValue.unavailable("bytes")
        ),
        available_memory_bytes=(
            _measured(available)
            if available is not None
            else ResourceValue.unavailable("bytes")
        ),
        process_rss_bytes=_measured(123),
    )


class _Observer:
    def __init__(self, snapshots):
        self.snapshots = deque(snapshots)

    def snapshot(self):
        return self.snapshots.popleft()


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _cfg(key: str):
    return {
        "model": key,
        "model_id": f"org/{key}",
        "backend": "fake",
        "modalities": ["text"],
        "max_concurrent_requests": 1,
    }


def _app(*, admin: bool, observer=None):
    manager = ProductRuntimeManager(default_model="default")
    manager.add(_cfg("default"), _Engine())
    manager.add(_cfg("old"), _Engine())
    application = create_app(
        manager,
        settings=ServerSettings(enable_admin_api=admin),
    )
    install_pressure_dry_run_api(
        application,
        observer=observer,
        policy=PressureEvictionPolicy(),
    )
    return application, manager


def test_two_critical_samples_trigger_candidate_without_unloading_runtime():
    observer = _Observer([
        _snapshot(available=50),
        _snapshot(available=50),
    ])
    application, manager = _app(admin=True, observer=observer)
    client = TestClient(application)

    first = client.post("/api/v1/residency/pressure/evaluate")
    second = client.post("/api/v1/residency/pressure/evaluate")

    assert first.status_code == 200
    assert first.json()["evaluation"]["pressure"] == "critical"
    assert first.json()["evaluation"]["state"] == "watching"
    assert first.json()["evaluation"]["should_attempt_eviction"] is False

    payload = second.json()
    assert payload["mode"] == "dry_run"
    assert payload["action_executed"] is False
    assert payload["evaluation"]["state"] == "triggered"
    assert payload["evaluation"]["transition"] == "triggered"
    assert payload["evaluation"]["should_attempt_eviction"] is True
    assert [item["key"] for item in payload["evaluation"]["candidates"]] == ["old"]
    assert payload["evaluation"]["automatic_eviction_enabled"] is False
    assert payload["evaluation"]["reclamation_claim"] is False
    assert "No runtime was unloaded" in payload["claim_boundary"]

    assert sorted(runtime.key for runtime in manager.list()) == ["default", "old"]
    assert manager.default_model == "default"


def test_dry_run_exposes_host_memory_sources_but_not_process_rss():
    application, _ = _app(
        admin=True,
        observer=_Observer([_snapshot(available=500)]),
    )
    payload = TestClient(application).post(
        "/api/v1/residency/pressure/evaluate"
    ).json()

    assert payload["resource"] == {
        "platform": "test",
        "total_memory_bytes": {
            "value": 1_000,
            "source": "measured",
            "unit": "bytes",
        },
        "available_memory_bytes": {
            "value": 500,
            "source": "measured",
            "unit": "bytes",
        },
        "thermal_pressure": {
            "value": None,
            "source": "unavailable",
            "unit": "level",
        },
    }
    assert "process_rss" not in str(payload["resource"])


def test_unknown_resource_observation_never_triggers_candidate():
    application, manager = _app(
        admin=True,
        observer=_Observer([_snapshot(available=None)]),
    )
    payload = TestClient(application).post(
        "/api/v1/residency/pressure/evaluate"
    ).json()

    assert payload["evaluation"]["pressure"] == "unknown"
    assert payload["evaluation"]["should_attempt_eviction"] is False
    assert payload["evaluation"]["candidates"] == []
    assert len(manager.list()) == 2


def test_pressure_dry_run_route_is_admin_only():
    application, _ = _app(
        admin=False,
        observer=_Observer([_snapshot(available=50)]),
    )
    client = TestClient(application)

    assert client.post("/api/v1/residency/pressure/evaluate").status_code == 404


def test_pressure_evaluation_requires_post_because_it_advances_hysteresis_state():
    application, _ = _app(
        admin=True,
        observer=_Observer([_snapshot(available=50)]),
    )
    client = TestClient(application)

    assert client.get("/api/v1/residency/pressure/evaluate").status_code == 405
