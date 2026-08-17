#!/usr/bin/env python3
"""Exercise an assembled HTTP failure/retry/recovery journey from an installed wheel.

This file is launched by the Python interpreter inside the fresh package-smoke
venv. It starts the assembled application on a pre-bound localhost socket and
uses only the standard-library HTTP client, so the journey tests the installed
runtime surface without adding a test-client dependency to production.
"""
from __future__ import annotations

import http.client
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
from typing import Any

import uvicorn

import local_llm_server
from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.server import ServerSettings, create_app


class DeterministicInstalledEngine:
    backend = "installed-surface-fixture"
    backend_version = "1"

    def __init__(self) -> None:
        self.complete_calls = 0

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.complete_calls += 1
        return {
            "id": "chatcmpl-installed-surface",
            "object": "chat.completion",
            "model": str(payload.get("model") or "installed/runtime"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "42"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    def close(self) -> None:
        return None


def _assert_imported_from_installed_surface() -> str:
    module_file = Path(local_llm_server.__file__).resolve()
    raw_source_root = os.environ.get("LOCAL_LLM_SOURCE_ROOT")
    if not raw_source_root:
        raise RuntimeError("LOCAL_LLM_SOURCE_ROOT is required")
    source_root = Path(raw_source_root).resolve()
    if module_file == source_root or source_root in module_file.parents:
        raise AssertionError(f"journey imported source checkout instead of installed wheel: {module_file}")
    return str(module_file)


def _config() -> dict[str, Any]:
    return {
        "model": "installed-fixture",
        "model_id": "installed/runtime",
        "model_path": "/synthetic/installed-fixture.gguf",
        "backend": "installed-surface-fixture",
        "modalities": ["text"],
        "thinking_mode": "none",
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
        "default_temperature": 0.0,
        "default_top_p": 1.0,
        "default_top_k": 40,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "max_concurrent_requests": 1,
    }


def _json_request(port: int, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        parsed: dict[str, Any] = {}
        if raw:
            value = json.loads(raw.decode("utf-8"))
            if isinstance(value, dict):
                parsed = value
        return response.status, parsed
    finally:
        connection.close()


def _wait_until_started(server: uvicorn.Server, thread: threading.Thread, *, timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server.started:
            return
        if not thread.is_alive():
            raise RuntimeError("installed-surface Uvicorn server exited before startup")
        time.sleep(0.02)
    raise TimeoutError("installed-surface Uvicorn server did not start in time")


def run() -> dict[str, object]:
    installed_module = _assert_imported_from_installed_surface()
    engine = DeterministicInstalledEngine()
    manager = ProductRuntimeManager(default_model="installed-fixture")
    manager.add(_config(), engine)

    with tempfile.TemporaryDirectory(prefix="local-llm-installed-journey-") as raw_root:
        evaluation_root = Path(raw_root) / "evaluation"
        evaluation_root.mkdir()
        application = create_app(manager, settings=ServerSettings(enable_admin_api=True))
        install_product_http_stack(application, evaluation_root=evaluation_root)

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = int(listener.getsockname()[1])
        server = uvicorn.Server(
            uvicorn.Config(
                application,
                host="127.0.0.1",
                port=port,
                log_level="warning",
                lifespan="on",
                timeout_graceful_shutdown=2,
            )
        )
        thread = threading.Thread(
            target=server.run,
            kwargs={"sockets": [listener]},
            name="installed-surface-uvicorn",
            daemon=False,
        )
        thread.start()
        try:
            _wait_until_started(server, thread)

            healthy_before_status, healthy_before = _json_request(port, "GET", "/health")
            assert healthy_before_status == 200, healthy_before

            failed_status, failed = _json_request(
                port,
                "POST",
                "/v1/chat/completions",
                {
                    "model": "not-resident",
                    "messages": [{"role": "user", "content": "synthetic failure input"}],
                    "stream": False,
                },
            )
            assert failed_status == 404, failed

            retry_status, retry_payload = _json_request(
                port,
                "POST",
                "/v1/chat/completions",
                {
                    "model": "installed-fixture",
                    "messages": [{"role": "user", "content": "synthetic retry input"}],
                    "temperature": 0.0,
                    "stream": False,
                },
            )
            assert retry_status == 200, retry_payload
            assert retry_payload.get("content") == "42" or retry_payload.get("output") == "42"

            healthy_after_status, healthy_after = _json_request(port, "GET", "/health")
            assert healthy_after_status == 200, healthy_after
            assert engine.complete_calls == 1
        finally:
            server.should_exit = True
            thread.join(timeout=5.0)
            listener.close()
            if thread.is_alive():
                raise RuntimeError("installed-surface Uvicorn server did not stop cleanly")

        assert not any(evaluation_root.iterdir()), "installed journey left evaluation state"

    return {
        "schema_version": 1,
        "surface": "fresh-installed-wheel",
        "installed_module": installed_module,
        "transport": "real-localhost-http",
        "failure": {"kind": "model_not_resident", "status_code": 404},
        "retry": {"kind": "valid_resident_model", "status_code": 200},
        "recovery": {"health_after_failure_and_retry": True},
        "server_cleanup": {"thread_stopped": True},
        "model_downloaded": False,
        "prompt_or_output_retained": False,
    }


def main() -> int:
    payload = run()
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
