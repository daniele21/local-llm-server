from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from local_llm_server.control_plane_api import install_product_api
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def __init__(self):
        self.calls = 0

    def complete(self, payload):
        self.calls += 1
        return {
            "choices": [{"message": {"role": "assistant", "content": "wrong"}}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1},
        }

    def close(self):
        pass


def _dataset(*, test_set_id="my-set", version="1.0.0"):
    return {
        "schema_version": 1,
        "id": test_set_id,
        "version": version,
        "provenance": {"purpose": "api-test"},
        "samples": [
            {
                "id": f"sample-{index:02d}",
                "task": "chat",
                "input": f"Return only {index}",
                "expected": {"exact": str(index)},
            }
            for index in range(10)
        ],
    }


def _app(tmp_path: Path, *, admin=True):
    manager = ModelRuntimeManager(default_model="demo")
    engine = _Engine()
    manager.add(
        {
            "model": "demo",
            "model_id": "org/demo",
            "backend": "fake",
            "modalities": ["text"],
            "max_concurrent_requests": 1,
        },
        engine,
    )
    app = create_app(manager, settings=ServerSettings(enable_admin_api=admin))
    install_product_api(app, evaluation_root=tmp_path / "evaluations")
    return app, engine


def _upload(client: TestClient, payload: dict, *, replace=False):
    return client.post(
        "/api/v1/evaluation/test-sets/import",
        data={"replace": "true" if replace else "false"},
        files={
            "file": (
                "test-set.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )


def test_custom_dataset_upload_appears_in_catalog_and_executes_selected_version(tmp_path: Path):
    app, engine = _app(tmp_path)
    client = TestClient(app)

    imported = _upload(client, _dataset())
    assert imported.status_code == 200
    imported_payload = imported.json()["test_set"]
    assert imported_payload["id"] == "my-set"
    assert imported_payload["version"] == "1.0.0"
    assert imported_payload["sample_count"] == 10
    assert imported_payload["source"] == "custom"
    assert "path" not in str(imported_payload).lower()

    catalog = client.get("/api/v1/evaluation/test-sets")
    assert catalog.status_code == 200
    custom = [item for item in catalog.json()["test_sets"] if item["id"] == "my-set"]
    assert len(custom) == 1
    assert custom[0]["source"] == "custom"
    assert custom[0]["identity"] == imported_payload["identity"]

    run = client.post(
        "/api/v1/evaluation/runs",
        json={
            "model": "demo",
            "test_set_id": "my-set",
            "test_set_version": "1.0.0",
            "sample_count": 10,
            "seed": 0,
        },
    )
    assert run.status_code == 200
    report = run.json()["report"]
    assert report["manifest"]["test_set_id"] == "my-set"
    assert report["manifest"]["test_set_version"] == "1.0.0"
    assert report["manifest"]["test_set_identity"] == imported_payload["identity"]
    assert len(report["results"]) == 10
    assert engine.calls == 10


def test_multiple_custom_versions_require_explicit_version(tmp_path: Path):
    app, _ = _app(tmp_path)
    client = TestClient(app)
    assert _upload(client, _dataset(version="1.0.0")).status_code == 200
    assert _upload(client, _dataset(version="2.0.0")).status_code == 200

    response = client.post(
        "/api/v1/evaluation/runs",
        json={"model": "demo", "test_set_id": "my-set", "sample_count": 10},
    )
    assert response.status_code == 400
    assert "multiple versions" in str(response.json()["detail"])


def test_import_rejects_builtin_collision_duplicate_and_invalid_json(tmp_path: Path):
    app, _ = _app(tmp_path)
    client = TestClient(app)

    reserved = _upload(client, _dataset(test_set_id="general-purpose"))
    assert reserved.status_code == 400
    assert "reserved" in str(reserved.json()["detail"])

    assert _upload(client, _dataset()).status_code == 200
    duplicate = _upload(client, _dataset())
    assert duplicate.status_code == 409

    invalid = client.post(
        "/api/v1/evaluation/test-sets/import",
        files={"file": ("bad.json", b"{broken", "application/json")},
    )
    assert invalid.status_code == 400
    assert "invalid test-set JSON" in str(invalid.json()["detail"])


def test_custom_dataset_import_is_not_exposed_without_admin_api(tmp_path: Path):
    app, _ = _app(tmp_path, admin=False)
    response = _upload(TestClient(app), _dataset())
    assert response.status_code == 404
