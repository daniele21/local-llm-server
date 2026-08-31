from __future__ import annotations

from fastapi.testclient import TestClient

from local_llm_server.policy_evidence import (
    install_policy_evidence_api,
    policy_evidence_payload,
)
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.request_middleware import install_request_policy
from local_llm_server.request_resource_admission import install_request_resource_admission
from local_llm_server.resource_manager import ReservationKind, ResourceManager
from local_llm_server.resources import ResourceBudget
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def close(self) -> None:
        pass


def _manager() -> ProductRuntimeManager:
    resources = ResourceManager(ResourceBudget(limit_bytes=1_000, headroom_bytes=100))
    manager = ProductRuntimeManager(default_model="safe", resource_manager=resources)
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
            "resource_estimate_bytes": 300,
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
            "resource_estimate_bytes": 200,
        },
        _Engine(),
        key="opted-in",
    )
    resources.reserve("runtime:safe", 300, kind=ReservationKind.RESIDENT)
    resources.commit("runtime:safe")
    resources.reserve("request:safe:one", 50, kind=ReservationKind.TRANSIENT)
    resources.commit("request:safe:one")
    return manager


def test_policy_evidence_exposes_only_bounded_effective_flags_and_resource_state():
    manager = _manager()
    app = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_request_resource_admission(app)
    install_request_policy(app)

    payload = policy_evidence_payload(app)

    assert payload["canonical_request_policy_installed"] is True
    assert payload["request_resource_admission_installed"] is True
    assert payload["remote_media_default"] == "blocked"
    assert payload["trust_remote_code_default"] is False
    assert payload["resource_budget"] == {
        "limit_bytes": 1_000,
        "headroom_bytes": 100,
        "usable_bytes": 900,
        "resident_accounted_bytes": 300,
        "transient_accounted_bytes": 50,
    }
    runtimes = {item["key"]: item for item in payload["runtimes"]}
    assert runtimes["safe"]["allow_remote_media"] is False
    assert runtimes["safe"]["trust_remote_code"] is False
    assert runtimes["safe"]["resident_memory_envelope"]["accounted_bytes"] == 300
    assert runtimes["safe"]["resident_memory_envelope"]["complete"] is True
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
    install_request_resource_admission(app)
    install_request_policy(app)
    install_policy_evidence_api(app)

    response = TestClient(app).get("/api/v1/policies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_request_policy_installed"] is True
    assert payload["request_resource_admission_installed"] is True
    assert len(payload["runtimes"]) == 2
    assert payload["resource_budget"]["transient_accounted_bytes"] == 50
    assert "/private/models" not in response.text
