from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from starlette.requests import Request

from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.server import (
    ServerSettings,
    begin_app_shutdown,
    create_app,
    stream_logs,
)


class _Engine:
    backend = "fake"

    def complete(self, payload):
        return {
            "choices": [{"message": {"role": "assistant", "content": payload["model"]}}]
        }

    def stream(self, payload):
        yield {"choices": [{"delta": {"content": payload["model"]}}]}

    def close(self):
        pass


def _manager(key: str) -> ModelRuntimeManager:
    manager = ModelRuntimeManager(default_model=key)
    manager.add(
        {
            "model": key,
            "model_id": f"org/{key}",
            "model_path": f"/{key}",
            "backend": "fake",
            "host": "127.0.0.1",
            "port": 1235,
            "modalities": ["text"],
            "default_temperature": 0.0,
            "default_top_p": 1.0,
            "default_top_k": 0,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "force_json": False,
        },
        _Engine(),
    )
    return manager


def test_create_app_keeps_runtime_state_isolated():
    first = create_app(_manager("first"))
    second = create_app(_manager("second"))

    with TestClient(first) as first_client, TestClient(second) as second_client:
        assert first_client.get("/health").json()["model"] == "org/first"
        assert second_client.get("/health").json()["model"] == "org/second"
    assert first.state.log_buffer is not second.state.log_buffer
    first.state.log_buffer.append("first only")
    assert list(second.state.log_buffer.buffer) == []


def test_admin_routes_are_opt_in():
    disabled = create_app(_manager("disabled"))
    enabled = create_app(
        _manager("enabled"),
        settings=ServerSettings(enable_admin_api=True),
    )

    with TestClient(disabled) as disabled_client, TestClient(enabled) as enabled_client:
        assert disabled_client.get("/api/v1/models/registry").status_code == 404
        assert enabled_client.get("/api/v1/models/registry").status_code == 200
        assert disabled_client.get("/health").json()["admin_api_enabled"] is False
        assert enabled_client.get("/health").json()["admin_api_enabled"] is True


def test_cors_is_disabled_by_default_and_explicit_when_enabled():
    disabled = create_app(_manager("disabled"))
    enabled = create_app(
        _manager("enabled"),
        settings=ServerSettings(cors_origins=("https://app.example",)),
    )
    headers = {
        "Origin": "https://app.example",
        "Access-Control-Request-Method": "POST",
    }

    with TestClient(disabled) as disabled_client, TestClient(enabled) as enabled_client:
        assert "access-control-allow-origin" not in disabled_client.options(
            "/v1/chat/completions", headers=headers
        ).headers
        assert enabled_client.options(
            "/v1/chat/completions", headers=headers
        ).headers["access-control-allow-origin"] == "https://app.example"


def test_shutdown_notification_stops_log_sse_before_lifespan_teardown():
    application = create_app(
        _manager("logs"),
        settings=ServerSettings(enable_admin_api=True),
    )
    request = Request({"type": "http", "app": application})
    response = stream_logs(request)

    begin_app_shutdown(application)

    async def consume():
        return [chunk async for chunk in response.body_iterator]

    assert asyncio.run(consume()) == []
