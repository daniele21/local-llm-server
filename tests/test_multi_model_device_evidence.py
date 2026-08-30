from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import pytest

from local_llm_server.multi_model_device_evidence import (
    MultiModelDeviceEvidenceOptions,
    execute_multi_model_device_evidence,
    write_multi_model_evidence_report,
)
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


class _Observer:
    def __init__(self, *, available: int = 10_000):
        self.available = available
        self.calls = 0

    def snapshot(self):
        self.calls += 1
        return SystemResourceSnapshot(
            captured_at_monotonic=float(self.calls),
            platform="darwin",
            total_memory_bytes=_measured(20_000),
            available_memory_bytes=_measured(self.available),
            process_rss_bytes=_measured(1_000 + self.calls),
        )


class _Engine:
    backend = "fake"

    def __init__(self, inference_barrier: threading.Barrier):
        self.inference_barrier = inference_barrier
        self.calls = 0
        self.closed = False

    def complete(self, payload):
        self.calls += 1
        self.inference_barrier.wait(timeout=5.0)
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


def _cfg(model: str, **kwargs):
    estimate = 400 if model == "model-a" else 500
    return {
        "model": model,
        "model_id": f"org/{model}",
        "model_path": f"/private/{model}.gguf",
        "backend": "fake",
        "resource_estimate_bytes": estimate,
        "resource_request_estimate_bytes": kwargs.get("resource_request_estimate_bytes"),
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
        "max_concurrent_requests": kwargs.get("max_concurrent_requests", 1),
    }


def _options(**overrides):
    values = {
        "model_a": "model-a",
        "model_b": "model-b",
        "request_estimate_bytes": 50,
        "cycles": 1,
        "headroom_bytes": 100,
        "success_margin_bytes": 100,
        "host_safety_bytes": 100,
        "settle_seconds": 0,
        "shutdown_timeout_seconds": 0,
        "sample_interval_seconds": 0.001,
        "prompt": "PRIVATE RRG5 PROMPT",
    }
    values.update(overrides)
    return MultiModelDeviceEvidenceOptions(**values)


def _receipt(cfg):
    char = "a" if cfg["model"] == "model-a" else "b"
    return SimpleNamespace(sha256=char * 64)


def test_campaign_exercises_two_models_concurrent_accounting_and_shutdown_retry(monkeypatch):
    inference_barrier = threading.Barrier(2)
    engines: list[_Engine] = []

    def fake_build_config(model=None, model_path=None, **kwargs):
        del model_path
        return _cfg(str(model), **kwargs)

    def load_backend(cfg):
        del cfg
        engine = _Engine(inference_barrier)
        engines.append(engine)
        return engine

    monkeypatch.setattr("local_llm_server.config.build_config", fake_build_config)
    monkeypatch.setattr("local_llm_server.engine.load_llm", load_backend)

    report = execute_multi_model_device_evidence(
        _options(),
        observer=_Observer(),
        config_builder=fake_build_config,
        receipt_resolver=_receipt,
        backend_rss_reader=lambda _pid: ResourceValue.unavailable("bytes"),
        sleep=lambda _seconds: None,
    )

    assert report["complete"] is True
    assert report["status"] == "complete"
    assert len(report["cycles"]) == 1
    [cycle] = report["cycles"]
    assert cycle["complete"] is True
    assert cycle["concurrent_transient_overlap_observed"] is True
    assert cycle["configured_accounting_peak"]["resident_committed_bytes"] == 900
    assert cycle["configured_accounting_peak"]["transient_committed_bytes"] == 100
    assert cycle["configured_accounting_after_unload"]["reservation_count"] == 0
    assert {item["http_status"] for item in cycle["responses"]} == {200}
    assert cycle["pressure_policy_dry_run"]["automatic_eviction_enabled"] is False
    assert cycle["automatic_eviction_exercised"] is False

    shutdown = report["shutdown_under_load"]
    assert shutdown["complete"] is True
    assert shutdown["first_shutdown_reported_incomplete"] is True
    assert shutdown["active_owner_retained_after_timeout"] is True
    assert shutdown["configured_accounting_after_first_shutdown"]["resident_committed_bytes"] == 400
    assert shutdown["configured_accounting_after_retry"]["reservation_count"] == 0
    assert report["automatic_eviction_exercised"] is False
    assert all(engine.closed for engine in engines)

    rendered = json.dumps(report)
    assert "PRIVATE RRG5 PROMPT" not in rendered
    assert "/private/" not in rendered
    assert "pid" not in rendered.lower()


def test_campaign_refuses_low_host_memory_before_backend_load(monkeypatch):
    backend_loads = []

    def fake_build_config(model=None, model_path=None, **kwargs):
        del model_path
        return _cfg(str(model), **kwargs)

    monkeypatch.setattr("local_llm_server.config.build_config", fake_build_config)
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: backend_loads.append(cfg) or _Engine(threading.Barrier(2)),
    )

    report = execute_multi_model_device_evidence(
        _options(),
        observer=_Observer(available=1_000),
        config_builder=fake_build_config,
        receipt_resolver=_receipt,
        sleep=lambda _seconds: None,
    )

    assert report["status"] == "refused_host_safety"
    assert report["complete"] is False
    assert backend_loads == []


def test_campaign_requires_verified_artifacts_before_backend_load(monkeypatch):
    backend_loads = []

    def fake_build_config(model=None, model_path=None, **kwargs):
        del model_path
        return _cfg(str(model), **kwargs)

    monkeypatch.setattr("local_llm_server.config.build_config", fake_build_config)
    monkeypatch.setattr(
        "local_llm_server.engine.load_llm",
        lambda cfg: backend_loads.append(cfg) or _Engine(threading.Barrier(2)),
    )

    with pytest.raises(RuntimeError, match="verified artifact receipt"):
        execute_multi_model_device_evidence(
            _options(),
            observer=_Observer(),
            config_builder=fake_build_config,
            receipt_resolver=lambda _cfg: None,
        )

    assert backend_loads == []


def test_campaign_rejects_same_model_key_and_invalid_request_estimate():
    with pytest.raises(ValueError, match="distinct model keys"):
        MultiModelDeviceEvidenceOptions(
            model_a="same",
            model_b="same",
            request_estimate_bytes=1,
        )
    with pytest.raises(ValueError, match="request_estimate_bytes"):
        MultiModelDeviceEvidenceOptions(
            model_a="a",
            model_b="b",
            request_estimate_bytes=0,
        )


def test_report_writer_is_atomic(tmp_path):
    output = write_multi_model_evidence_report(
        tmp_path / "rrg5.json",
        {"schema_version": 1, "complete": False},
    )
    assert json.loads(output.read_text(encoding="utf-8"))["complete"] is False
    assert not (tmp_path / "rrg5.json.tmp").exists()
