from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.residency_api import install_residency_api
from local_llm_server.residency_eviction import (
    EvictionMode,
    EvictionPolicySettings,
    select_eviction_candidates,
)
from local_llm_server.server import ServerSettings


def _snapshot() -> dict:
    return {
        "resident_default_model": "a",
        "runtimes": [
            {
                "key": "a",
                "model": "org/a",
                "state": "ready",
                "active_requests": 0,
                "pinned": False,
                "evictable": True,
                "is_resident_default": True,
                "last_used_age_seconds": 100.0,
            },
            {
                "key": "b",
                "model": "org/b",
                "state": "ready",
                "active_requests": 0,
                "pinned": False,
                "evictable": True,
                "is_resident_default": False,
                "last_used_age_seconds": 80.0,
            },
            {
                "key": "c",
                "model": "org/c",
                "state": "ready",
                "active_requests": 0,
                "pinned": False,
                "evictable": True,
                "is_resident_default": False,
                "last_used_age_seconds": 20.0,
            },
            {
                "key": "pinned",
                "model": "org/pinned",
                "state": "ready",
                "active_requests": 0,
                "pinned": True,
                "evictable": False,
                "is_resident_default": False,
                "last_used_age_seconds": 200.0,
            },
        ],
    }


def test_lru_selection_is_oldest_first_and_protects_resident_default():
    candidates = select_eviction_candidates(
        _snapshot(),
        EvictionPolicySettings(mode=EvictionMode.LRU, limit=2),
    )

    assert [candidate.key for candidate in candidates] == ["b", "c"]
    assert all(candidate.is_resident_default is False for candidate in candidates)


def test_lru_can_include_default_only_when_explicitly_requested():
    candidates = select_eviction_candidates(
        _snapshot(),
        EvictionPolicySettings(
            mode=EvictionMode.LRU,
            limit=1,
            protect_resident_default=False,
        ),
    )

    assert [candidate.key for candidate in candidates] == ["a"]


def test_ttl_selection_applies_age_threshold_and_never_reintroduces_non_evictable():
    candidates = select_eviction_candidates(
        _snapshot(),
        EvictionPolicySettings(
            mode=EvictionMode.TTL,
            limit=8,
            ttl_seconds=50.0,
        ),
    )

    assert [candidate.key for candidate in candidates] == ["b"]
    assert all(candidate.key != "pinned" for candidate in candidates)


def test_ttl_requires_explicit_nonnegative_threshold():
    try:
        EvictionPolicySettings(mode=EvictionMode.TTL)
    except ValueError as exc:
        assert "ttl_seconds" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_product_runtime_snapshot_exposes_recency_without_changing_evictable_contract():
    class Engine:
        backend = "fake"

        def close(self):
            pass

    cfg = {
        "model": "a",
        "model_id": "org/a",
        "backend": "fake",
        "modalities": ["text"],
        "max_concurrent_requests": 1,
    }
    manager = ProductRuntimeManager(default_model="a")
    runtime = manager.add(cfg, Engine(), key="a")

    snapshot = manager.residency_policy_snapshot()
    item = snapshot["runtimes"][0]
    assert item["is_resident_default"] is True
    assert item["last_used_age_seconds"] >= 0
    assert item["evictable"] is True

    with manager.lease_runtime(runtime):
        leased = manager.residency_policy_snapshot()["runtimes"][0]
        assert leased["active_requests"] == 1
        assert leased["evictable"] is False


class _SkipManager:
    def residency_policy_snapshot(self):
        return {
            "configured_default_model": "a",
            "resident_default_model": "a",
            "cold": False,
            "runtimes": [
                {
                    "key": "b",
                    "model": "org/b",
                    "state": "ready",
                    "active_requests": 0,
                    "pinned": False,
                    "evictable": True,
                    "is_resident_default": False,
                    "last_used_age_seconds": 90.0,
                }
            ],
        }

    def unload(self, model: str):
        raise RuntimeError("lease started after selection")


def _residency_app(manager) -> FastAPI:
    app = FastAPI()
    app.state.settings = ServerSettings(enable_admin_api=True)
    app.state.runtime_manager = manager
    install_residency_api(app)
    return app


def test_preview_is_explicit_nonautomatic_and_makes_no_reclamation_claim():
    response = TestClient(_residency_app(_SkipManager())).post(
        "/api/v1/residency/eviction/preview",
        json={"mode": "lru", "limit": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_count"] == 1
    assert payload["candidates"][0]["key"] == "b"
    assert payload["automatic"] is False
    assert payload["reclamation_claim"] is False


def test_explicit_eviction_skips_runtime_when_state_changes_after_selection():
    response = TestClient(_residency_app(_SkipManager())).post(
        "/api/v1/residency/evict",
        json={"mode": "lru", "limit": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["evicted"] == []
    assert payload["skipped"] == [
        {"key": "b", "model": "org/b", "reason": "RuntimeError"}
    ]
    assert payload["automatic"] is False
    assert payload["reclamation_claim"] is False


def test_ttl_preview_rejects_missing_threshold():
    response = TestClient(_residency_app(_SkipManager())).post(
        "/api/v1/residency/eviction/preview",
        json={"mode": "ttl"},
    )

    assert response.status_code == 422
    assert "ttl_seconds" in response.text
