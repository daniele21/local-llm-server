#!/usr/bin/env python3
"""Exercise an assembled HTTP failure/retry/recovery journey from an installed wheel.

This file is launched by the Python interpreter inside the fresh package-smoke
venv. It intentionally uses a deterministic in-process engine so packaging and
product assembly are tested without downloading or executing a model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from fastapi.testclient import TestClient

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

        with TestClient(application, raise_server_exceptions=False) as client:
            healthy_before = client.get("/health")
            assert healthy_before.status_code == 200

            failed = client.post(
                "/v1/chat/completions",
                json={
                    "model": "not-resident",
                    "messages": [{"role": "user", "content": "synthetic failure input"}],
                    "stream": False,
                },
            )
            assert failed.status_code == 404, failed.text

            retry = client.post(
                "/v1/chat/completions",
                json={
                    "model": "installed-fixture",
                    "messages": [{"role": "user", "content": "synthetic retry input"}],
                    "temperature": 0.0,
                    "stream": False,
                },
            )
            assert retry.status_code == 200, retry.text
            retry_payload = retry.json()
            assert retry_payload.get("content") == "42" or retry_payload.get("output") == "42"

            healthy_after = client.get("/health")
            assert healthy_after.status_code == 200
            assert engine.complete_calls == 1

        assert not any(evaluation_root.iterdir()), "installed journey left evaluation state"

    return {
        "schema_version": 1,
        "surface": "fresh-installed-wheel",
        "installed_module": installed_module,
        "failure": {"kind": "model_not_resident", "status_code": 404},
        "retry": {"kind": "valid_resident_model", "status_code": 200},
        "recovery": {"health_after_failure_and_retry": True},
        "model_downloaded": False,
        "prompt_or_output_retained": False,
    }


def main() -> int:
    payload = run()
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
