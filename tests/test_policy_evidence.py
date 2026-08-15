from __future__ import annotations

from fastapi.testclient import TestClient

from local_llm_server.policy_evidence import (
    install_policy_evidence_api,
    policy_evidence_payload,
)
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.request_middleware import install_request_policy
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def close(self) -> None:
        pass


def _manager() -> ProductRuntimeManager:
    manager = ProductRuntimeManager(default_model="safe")
    manager.add(
        {
            "model": "safe",
            "model_id": "org/safe",
            "backend": "fake",
            "modalities": ["text"],
            "max_concurrent_requests": 1,
            "allow_remote_media": False,
            "trust_remote_code": False,
            "model_path": "/private/models/secret.gguf",
        },
        _Engine(),
        key="safe",
    )
    manager.add(
        {
            "model": "opted-in",
            "model_id": "org/opted-in",
            "backend": "fake",
            "modalities": ["text", "image"],
            "max_concurrent_requests": 1,
            "allow_remote_media": True,
            "trust_remote_code": True,
            "model_path": "/private/models/other-secret.gguf",
        },
        _Engine(),
        key="opted-in",
    )
    return manager


def test_policy_evidence_exposes_only_bounded_effective_flags():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_request_policy(app)

    payload = policy_evidence_payload(app)

    assert payload["canonical_request_policy_installed"] is True
    assert payload["remote_media_default"] == "blocked"
    assert payload["trust_remote_code_default"] is False
    runtimes = {item["key"]: item for item in payload["runtimes"]}
    assert runtimes["safe"]["allow_remote_media"] is False
    assert runtimes["safe"]["trust_remote_code"] is False
    assert runtimes["opted-in"]["allow_remote_media"] is True
    assert runtimes["opted-in"]["trust_remote_code"] is True
    serialized = str(payload)
    assert "/private/models" not in serialized
    assert "model_path" not in serialized


def test_policy_evidence_api_is_admin_only():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=False))
    install_policy_evidence_api(app)

    assert TestClient(app).get("/api/v1/policies").status_code == 404


def test_policy_evidence_api_returns_runtime_policy_without_paths():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_request_policy(app)
    install_policy_evidence_api(app)

    response = TestClient(app).get("/api/v1/policies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_request_policy_installed"] is True
    assert len(payload["runtimes"]) == 2
    assert "/private/models" not in response.text
