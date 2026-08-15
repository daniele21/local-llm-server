from __future__ import annotations

from fastapi.testclient import TestClient

from local_llm_server.control_plane_api import install_product_api
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.resource_policy import ResourcePolicySettings
from local_llm_server.runtime import RuntimeState
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def _cfg(key: str) -> dict:
    return {
        "model": key,
        "model_id": f"org/{key}",
        "model_path": f"/models/{key}",
        "backend": "fake",
        "host": "127.0.0.1",
        "port": 1235,
        "max_concurrent_requests": 1,
        "modalities": ["text"],
        "default_temperature": 0.0,
        "default_top_p": 1.0,
        "default_top_k": 40,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "thinking_mode": "none",
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
    }


def test_last_runtime_can_unload_while_configured_default_survives():
    engine = _Engine()
    manager = ProductRuntimeManager(default_model="primary")
    runtime = manager.add(_cfg("primary"), engine)

    unloaded = manager.unload("primary")

    assert unloaded is runtime
    assert unloaded.state is RuntimeState.STOPPED
    assert engine.closed is True
    assert manager.list() == []
    assert manager.cold is True
    assert manager.default_model is None
    assert manager.configured_default_model == "primary"

    try:
        manager.resolve()
    except LookupError as exc:
        assert "configured default" in str(exc).lower()
        assert "primary" in str(exc)
    else:
        raise AssertionError("expected cold default resolution to fail")


def test_loading_unrelated_runtime_does_not_replace_cold_configured_route():
    manager = ProductRuntimeManager(default_model="primary")
    manager.add(_cfg("secondary"), _Engine())

    assert manager.default_model is None
    assert manager.configured_default_model == "primary"
    assert manager.resolve("secondary").key == "secondary"

    primary = manager.add(_cfg("primary"), _Engine())
    assert manager.default_model == "primary"
    assert manager.resolve() is primary


def test_configured_default_is_restored_after_reload_while_fallback_is_resident():
    manager = ProductRuntimeManager(default_model="primary")
    manager.add(_cfg("primary"), _Engine())
    secondary = manager.add(_cfg("secondary"), _Engine())

    manager.unload("primary")
    assert manager.default_model == "secondary"
    assert manager.resolve() is secondary
    assert manager.configured_default_model == "primary"

    primary = manager.add(_cfg("primary"), _Engine())
    assert manager.default_model == "primary"
    assert manager.resolve() is primary


def test_set_default_updates_configured_and_resident_identity():
    manager = ProductRuntimeManager(default_model="primary")
    manager.add(_cfg("primary"), _Engine())
    secondary = manager.add(_cfg("secondary"), _Engine())

    manager.set_default("secondary")

    assert manager.default_model == "secondary"
    assert manager.configured_default_model == "secondary"
    assert manager.resolve() is secondary


def test_shutdown_clears_residency_but_preserves_configured_identity():
    manager = ProductRuntimeManager(default_model="primary")
    manager.add(_cfg("primary"), _Engine())

    manager.shutdown()

    assert manager.list() == []
    assert manager.default_model is None
    assert manager.configured_default_model == "primary"


def test_admin_unload_last_model_keeps_product_health_green_and_cold(tmp_path):
    engine = _Engine()
    manager = ProductRuntimeManager(default_model="primary")
    manager.add(_cfg("primary"), engine)
    application = create_app(
        manager,
        settings=ServerSettings(enable_admin_api=True),
    )
    application.state.resource_policy_settings = ResourcePolicySettings()
    install_product_api(application, evaluation_root=tmp_path / "eval")
    client = TestClient(application)

    response = client.delete("/api/v1/models/primary")
    assert response.status_code == 200
    assert engine.closed is True

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.json()["state"] == "cold"
    assert health.json()["resident"] is False
    assert health.json()["configured_default_model"] == "primary"
    assert health.json()["default_model"] is None

    models = client.get("/v1/models")
    assert models.status_code == 200
    assert models.json()["data"] == []

    status = client.get("/status")
    assert status.status_code == 200
    assert status.json()["models"] == {}
    assert status.json()["default_model"] is None

    evidence = client.get("/api/v1/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["cold"] is True
    assert evidence.json()["runtime_count"] == 0
    assert evidence.json()["configured_default_model"] == "primary"
    assert evidence.json()["default_model"] is None

    assert application.state.llm is None
    assert application.state.cfg is None
