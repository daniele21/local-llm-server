from __future__ import annotations

from local_llm_server.resource_policy_smoke import (
    ResourcePolicySmokeOptions,
    execute_resource_policy_smoke,
    write_smoke_report,
)
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)


class _Observer:
    def __init__(self, available: int):
        self.available = available

    def snapshot(self):
        return SystemResourceSnapshot(
            captured_at_monotonic=1.0,
            platform="darwin",
            total_memory_bytes=ResourceValue(
                32_000,
                ResourceValueSource.MEASURED,
                "bytes",
            ),
            available_memory_bytes=ResourceValue(
                self.available,
                ResourceValueSource.MEASURED,
                "bytes",
            ),
        )


class _Engine:
    backend = "fake"

    def __init__(self):
        self.calls = 0
        self.closed = False

    def complete(self, payload):
        self.calls += 1
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "OK"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1},
        }

    def stream(self, payload):
        yield {"choices": [{"delta": {"content": "OK"}}]}

    def close(self):
        self.closed = True


def _cfg():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": "/private/model.gguf",
        "backend": "fake",
        "resource_estimate_bytes": 400,
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


def test_bounded_smoke_exercises_real_product_lifecycle_without_pressure(monkeypatch):
    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: dict(_cfg()),
    )
    backend_loads = []

    def load_backend(cfg):
        engine = _Engine()
        backend_loads.append(engine)
        return engine

    monkeypatch.setattr("local_llm_server.engine.load_llm", load_backend)

    report = execute_resource_policy_smoke(
        ResourcePolicySmokeOptions(
            model="demo",
            prompt="private prompt that must not enter report",
            max_tokens=4,
            headroom_bytes=100,
            success_margin_bytes=100,
            host_safety_bytes=100,
        ),
        observer=_Observer(10_000),
    )

    assert report["success"]["admission"] == "admit"
    assert report["success"]["inference_http_status"] == 200
    assert report["success"]["committed_bytes"] == 400
    assert report["success"]["committed_bytes_after_unload"] == 0
    assert report["success"]["reserved_bytes_after_unload"] == 0
    assert report["success"]["health_ok_after_unload"] is True
    assert report["success"]["health_state_after_unload"] == "cold"
    assert report["rejection"]["admission"] == "reject"
    assert report["rejection"]["backend_load_reached"] is False
    assert report["automatic_eviction_exercised"] is False
    # Exactly one backend load proves the insufficient-budget branch rejected
    # before engine construction.
    assert len(backend_loads) == 1
    rendered = str(report)
    assert "private prompt" not in rendered
    assert "/private/model.gguf" not in rendered


def test_safety_gate_refuses_smoke_before_any_backend_load(monkeypatch):
    monkeypatch.setattr(
        "local_llm_server.config.build_config",
        lambda **_kwargs: dict(_cfg()),
    )
    backend_loads = []
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: backend_loads.append(cfg) or _Engine(),
    )

    try:
        execute_resource_policy_smoke(
            ResourcePolicySmokeOptions(
                model="demo",
                headroom_bytes=100,
                success_margin_bytes=500,
                host_safety_bytes=500,
            ),
            observer=_Observer(1_000),
        )
    except RuntimeError as exc:
        assert "refused" in str(exc)
    else:
        raise AssertionError("expected host-memory safety gate to refuse the smoke")

    assert backend_loads == []


def test_smoke_report_writer_is_atomic_and_path_content_is_caller_owned(tmp_path):
    report = {"schema_version": 1, "procedure": "bounded_resource_policy_smoke"}
    output = write_smoke_report(tmp_path / "resource-smoke.json", report)

    assert output.exists()
    assert "bounded_resource_policy_smoke" in output.read_text(encoding="utf-8")
    assert not (tmp_path / "resource-smoke.json.tmp").exists()
