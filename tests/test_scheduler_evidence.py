from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from local_llm_server.control_plane_api import install_product_api
from local_llm_server.core.contracts import InferenceRequest, TaskType
from local_llm_server.request_scheduler import RuntimeGateRegistry, install_request_scheduler
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.scheduler_evidence import scheduler_evidence_payload
from local_llm_server.scheduler_policy import RequestSchedulerSettings
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _manager():
    manager = ModelRuntimeManager(default_model="demo")
    manager.add(
        {
            "model": "demo",
            "model_id": "org/demo",
            "backend": "fake",
            "modalities": ["text"],
            "max_concurrent_requests": 1,
        },
        _Engine(),
    )
    return manager


def test_disabled_scheduler_evidence_is_explicit_not_fake_zero():
    async def scenario():
        manager = _manager()
        app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
        app.state.request_scheduler_settings = RequestSchedulerSettings()
        app.state.runtime_gate_registry = None

        payload = await scheduler_evidence_payload(app)

        assert payload["policy"]["enabled"] is False
        assert payload["policy"]["queue_capacity"] is None
        assert payload["runtimes"] == []

    asyncio.run(scenario())


def test_scheduler_evidence_reports_aggregate_running_and_queued_without_request_ids():
    async def scenario():
        manager = _manager()
        settings = RequestSchedulerSettings(queue_capacity=2)
        registry = RuntimeGateRegistry(settings)
        app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
        app.state.request_scheduler_settings = settings
        app.state.runtime_gate_registry = registry
        runtime = manager.resolve("demo")
        gate = registry.gate_for(runtime)
        request = InferenceRequest(task=TaskType.CHAT, model="demo", input_text="secret prompt")

        await gate.acquire("private-running-id", request)
        queued = asyncio.create_task(gate.acquire("private-queued-id", request))
        await asyncio.sleep(0)

        payload = await scheduler_evidence_payload(app)
        runtime_payload = payload["runtimes"][0]
        assert runtime_payload["inflight"] == 1
        assert runtime_payload["queued"] == 1
        assert runtime_payload["max_running"] == 1
        assert runtime_payload["queue_capacity"] == 2
        rendered = str(payload)
        assert "private-running-id" not in rendered
        assert "private-queued-id" not in rendered
        assert "secret prompt" not in rendered

        queued.cancel()
        try:
            await queued
        except asyncio.CancelledError:
            pass
        await gate.release("private-running-id")

    asyncio.run(scenario())


def test_admin_control_plane_exposes_scheduler_source(tmp_path):
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_request_scheduler(
        app,
        settings=RequestSchedulerSettings(queue_capacity=3, default_queue_timeout_ms=250),
    )
    install_product_api(app, evaluation_root=tmp_path / "evaluations")

    response = TestClient(app).get("/api/v1/scheduler")

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy"]["enabled"] is True
    assert payload["policy"]["queue_capacity"] == 3
    assert payload["policy"]["default_queue_timeout_ms"] == 250
    assert payload["policy"]["timeout_scope"] == "queue_wait_only"
    assert payload["runtimes"][0]["runtime_key"] == "demo"
