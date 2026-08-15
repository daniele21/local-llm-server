from __future__ import annotations

from types import SimpleNamespace

import pytest

from local_llm_server.product_runtime import bootstrap_product_runtimes
from local_llm_server.resource_policy import ResourcePolicySettings


class _Engine:
    backend = "fake"

    def __init__(self, key):
        self.key = key
        self.closed = False

    def close(self):
        self.closed = True


def _patch_runtime_dependencies(monkeypatch, *, estimates=None):
    estimates = estimates or {"default": 100}
    monkeypatch.setattr(
        "local_llm_server.registry.load_registry",
        lambda: {
            "default_model": "default",
            "models": {},
            "models_dir": SimpleNamespace(),
        },
    )

    def build_config(model=None, model_path=None, **explicit):
        key = model or "default"
        return {
            "model": key,
            "model_id": f"org/{key}",
            "backend": "fake",
            "model_path": model_path or f"/models/{key}",
            "resource_estimate_bytes": estimates.get(key),
            "max_concurrent_requests": 1,
            "host": explicit.get("host", "127.0.0.1"),
            "port": explicit.get("port", 1235),
        }

    monkeypatch.setattr("local_llm_server.config.build_config", build_config)
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: _Engine(cfg["model"]),
    )


def test_single_model_load_is_accounted_when_policy_is_configured(monkeypatch):
    _patch_runtime_dependencies(monkeypatch, estimates={"default": 300})
    bootstrap = bootstrap_product_runtimes(
        explicit={"host": "127.0.0.1", "port": 1235},
        resource_policy=ResourcePolicySettings(memory_limit_bytes=1000, headroom_bytes=100),
    )

    assert bootstrap.manager.resource_manager is not None
    [reservation] = bootstrap.manager.resource_manager.snapshot()
    assert reservation.accounted_bytes == 300
    assert reservation.state.value == "committed"
    assert bootstrap.cfg["resource_admission"]["decision"] == "admit"
    assert bootstrap.resource_policy.enabled is True


def test_single_model_is_rejected_before_backend_when_initial_load_exceeds_budget(monkeypatch):
    calls = []
    _patch_runtime_dependencies(monkeypatch, estimates={"default": 950})
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: calls.append(cfg) or _Engine(cfg["model"]),
    )

    with pytest.raises(RuntimeError, match="budget"):
        bootstrap_product_runtimes(
            resource_policy=ResourcePolicySettings(memory_limit_bytes=1000, headroom_bytes=100),
        )

    assert calls == []


def test_disabled_policy_keeps_resource_manager_absent(monkeypatch):
    _patch_runtime_dependencies(monkeypatch)
    bootstrap = bootstrap_product_runtimes(resource_policy=ResourcePolicySettings())

    assert bootstrap.manager.resource_manager is None
    assert bootstrap.resource_policy.enabled is False
    assert bootstrap.cfg["resource_admission"]["decision"] == "unknown"


def test_multiple_models_share_one_budget_and_preserve_selected_default(monkeypatch):
    _patch_runtime_dependencies(monkeypatch, estimates={"a": 200, "b": 300})
    bootstrap = bootstrap_product_runtimes(
        models=["a", "b"],
        default_model="b",
        resource_policy=ResourcePolicySettings(memory_limit_bytes=1000),
    )

    assert bootstrap.manager.default_model == "b"
    assert {runtime.key for runtime in bootstrap.manager.list()} == {"a", "b"}
    reservations = bootstrap.manager.resource_manager.snapshot()
    assert sum(item.accounted_bytes for item in reservations) == 500


def test_model_path_cannot_be_applied_to_multiple_startup_models(monkeypatch):
    _patch_runtime_dependencies(monkeypatch)
    with pytest.raises(ValueError, match="cannot be combined"):
        bootstrap_product_runtimes(
            models=["a", "b"],
            model_path="/tmp/model.gguf",
        )
