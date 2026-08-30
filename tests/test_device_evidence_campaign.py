from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from local_llm_server import device_evidence_campaign as campaign_module
from local_llm_server.device_evidence_campaign import (
    DeviceEvidenceCampaign,
    _INCONCLUSIVE,
    _PASS,
    _phase,
    _safe_exception_text,
)
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)


def _args(tmp_path: Path, **overrides) -> argparse.Namespace:
    values = {
        "model_a": "model-a",
        "model_a_path": "/private/model-a.gguf",
        "model_b": "model-b",
        "model_b_path": "/private/model-b.gguf",
        "backend": "llama_cpp",
        "multi_model_backend": "llama_server",
        "request_estimate_mib": 64.0,
        "scope": "full",
        "host": "127.0.0.1",
        "port": 18000,
        "startup_timeout": 1.0,
        "request_timeout": 1.0,
        "evaluation_timeout": 1.0,
        "output_dir": str(tmp_path / "evidence"),
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def _snapshot() -> SystemResourceSnapshot:
    measured = lambda value: ResourceValue(value, ResourceValueSource.MEASURED, "bytes")
    return SystemResourceSnapshot(
        captured_at_monotonic=1.0,
        platform="darwin",
        total_memory_bytes=measured(32 * 1024**3),
        available_memory_bytes=measured(20 * 1024**3),
        process_rss_bytes=measured(100 * 1024**2),
    )


def _git_state(tmp_path: Path) -> dict:
    return {
        "revision": "a" * 40,
        "branch": "dev",
        "tracked_clean": True,
        "root": (tmp_path / "repo").resolve(),
    }


class _Observer:
    def snapshot(self):
        return _snapshot()


class _FakeServer:
    def __init__(self, **_kwargs):
        self.base_url = "http://127.0.0.1:18000"

    def start(self):
        return None

    def stop(self):
        return {
            "owned_process_started": True,
            "exit_code": 0,
            "graceful": True,
            "hard_kill_required": False,
            "listener_closed": True,
        }


def test_safe_exception_text_drops_private_paths() -> None:
    rendered = _safe_exception_text(RuntimeError("failed at /Users/alice/private/model.gguf"))
    assert rendered == "RuntimeError"
    assert "alice" not in rendered
    assert "model.gguf" not in rendered


def test_preflight_refuses_non_loopback_bind(monkeypatch, tmp_path: Path) -> None:
    args = _args(tmp_path, host="0.0.0.0")
    runner = DeviceEvidenceCampaign(args)
    monkeypatch.setattr(campaign_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(campaign_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(campaign_module, "MacOSResourceObserver", _Observer)
    monkeypatch.setattr(campaign_module, "_git_state", lambda: _git_state(tmp_path))
    monkeypatch.setattr(campaign_module, "_port_is_free", lambda _host, _port: True)

    result = runner._preflight()

    assert result["status"] == _INCONCLUSIVE
    assert result["checks"]["loopback_only"] is False


def test_preflight_refuses_full_scope_without_positive_request_estimate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    args = _args(tmp_path, request_estimate_mib=0.0)
    runner = DeviceEvidenceCampaign(args)
    monkeypatch.setattr(campaign_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(campaign_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(campaign_module, "MacOSResourceObserver", _Observer)
    monkeypatch.setattr(campaign_module, "_git_state", lambda: _git_state(tmp_path))
    monkeypatch.setattr(campaign_module, "_port_is_free", lambda _host, _port: True)

    result = runner._preflight()

    assert result["status"] == _INCONCLUSIVE
    assert result["checks"]["full_scope_inputs"] is False


def test_res2_safety_refusal_is_inconclusive_not_product_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    monkeypatch.setattr(
        campaign_module,
        "execute_resource_policy_smoke",
        lambda _options: (_ for _ in ()).throw(
            RuntimeError(
                "Bounded smoke refused: measured available host memory is below the artifact estimate plus configured success and host-safety margins."
            )
        ),
    )

    result = runner._run_phase("resource_policy_res_2", runner._resource_policy)

    assert result["status"] == _INCONCLUSIVE
    assert "refused" in result["reason"].lower()


def test_bundle_stays_inconclusive_when_a_real_environment_prerequisite_refuses(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    runner.summary["phases"].update(
        {
            "start_representative_server": _phase(_PASS, reason="ready"),
            "thinking_th_e1": _phase(_PASS, reason="ok"),
            "evaluation_ev_3": _phase(_PASS, reason="ok"),
            "reclamation_he_2": _phase(_PASS, reason="ok"),
            "resource_policy_res_2": _phase(_INCONCLUSIVE, reason="host safety"),
        }
    )
    monkeypatch.setattr(
        campaign_module,
        "validate_hardware_bundle",
        lambda _directory: {
            "complete": False,
            "gates": {"resource_policy_smoke": False},
            "errors": ["missing required evidence file: resource-policy-smoke.json"],
        },
    )

    result = runner._validate_l2_bundle()

    assert result["status"] == _INCONCLUSIVE
    assert runner.summary["minimum_l2_complete"] is False


def test_rrg5_host_safety_refusal_stops_without_second_heavy_run(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    calls = []

    def refused(_options):
        calls.append(1)
        return {
            "schema_version": 1,
            "status": "refused_host_safety",
            "complete": False,
            "automatic_eviction_exercised": False,
        }

    monkeypatch.setattr(campaign_module, "execute_multi_model_device_evidence", refused)

    result = runner._rrg5()

    assert result["status"] == _INCONCLUSIVE
    assert len(calls) == 1
    assert (runner.output_dir / "multimodel-a.json").is_file()
    assert not (runner.output_dir / "multimodel-b.json").exists()


def test_full_campaign_can_finish_green_without_leaking_private_inputs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    args = _args(tmp_path)
    runner = DeviceEvidenceCampaign(args)
    monkeypatch.setattr(campaign_module, "_OwnedServer", _FakeServer)

    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_preflight",
        lambda self: _phase(_PASS, reason="preflight ok"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_verify_primary",
        lambda self: _phase(_PASS, reason="primary verified"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_verify_secondary",
        lambda self: _phase(_PASS, reason="secondary verified"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_thinking",
        lambda self, _url: _phase(_PASS, reason="thinking ok"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_evaluation",
        lambda self, _url: _phase(_PASS, reason="evaluation ok"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_reclamation",
        lambda self: _phase(_PASS, reason="reclamation ok"),
    )
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_resource_policy",
        lambda self: _phase(_PASS, reason="resource ok"),
    )

    def validate(self):
        self.summary["minimum_l2_complete"] = True
        return _phase(_PASS, reason="bundle ok")

    def rrg5(self):
        self.summary["rrg5_complete"] = True
        return _phase(_PASS, reason="rrg5 ok")

    monkeypatch.setattr(DeviceEvidenceCampaign, "_validate_l2_bundle", validate)
    monkeypatch.setattr(DeviceEvidenceCampaign, "_rrg5", rrg5)
    monkeypatch.setattr(campaign_module.platform, "system", lambda: "Linux")

    exit_code = runner.run()

    assert exit_code == 0
    summary = json.loads(runner.summary_path.read_text(encoding="utf-8"))
    assert summary["complete"] is True
    assert summary["minimum_l2_complete"] is True
    assert summary["rrg5_complete"] is True
    rendered = json.dumps(summary)
    assert "/private/model-a.gguf" not in rendered
    assert "/private/model-b.gguf" not in rendered
    assert "process_ids_retained_in_summary" in rendered
    assert summary["automatic_eviction_exercised"] is False
    assert summary["production_safety_claim"] is False


def test_non_mac_preflight_exits_two_without_running_heavy_phases(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runner = DeviceEvidenceCampaign(_args(tmp_path))
    monkeypatch.setattr(campaign_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(campaign_module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(campaign_module, "_git_state", lambda: _git_state(tmp_path))
    monkeypatch.setattr(campaign_module, "_port_is_free", lambda _host, _port: True)
    monkeypatch.setattr(
        DeviceEvidenceCampaign,
        "_verify_primary",
        lambda self: pytest.fail("artifact verification must not run"),
    )

    exit_code = runner.run()

    assert exit_code == 2
    assert runner.summary["phases"]["preflight"]["status"] == _INCONCLUSIVE
    assert "verify_primary_artifact" not in runner.summary["phases"]
