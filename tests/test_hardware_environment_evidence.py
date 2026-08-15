from __future__ import annotations

import json

from local_llm_server.hardware_evidence import (
    HardwareEvidenceOptions,
    WorkerSystemResourceObserver,
    execute_hardware_reclamation_evidence,
    local_environment_metadata,
)
from local_llm_server.resources import ResourceValue, ResourceValueSource, SystemResourceSnapshot


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


class _Observer:
    def snapshot(self):
        return SystemResourceSnapshot(
            captured_at_monotonic=1.0,
            platform="test",
            total_memory_bytes=_measured(16 * 1024**3),
            available_memory_bytes=_measured(8 * 1024**3),
            process_rss_bytes=_measured(123),
        )


class _Report:
    def to_public_dict(self):
        return {
            "descriptor": {"identity_grade": "verified"},
            "experiment": {
                "cycle_count": 1,
                "complete_windows": 1,
                "error_cycles": 0,
                "observations": {
                    "recovery_observed": 1,
                    "no_recovery_observed": 0,
                    "inconclusive": 0,
                },
            },
        }


def test_local_environment_metadata_is_bounded_and_hostname_free(monkeypatch):
    monkeypatch.setattr("local_llm_server.hardware_evidence.platform.system", lambda: "Darwin")
    monkeypatch.setattr("local_llm_server.hardware_evidence.platform.release", lambda: "25.6.0")
    monkeypatch.setattr("local_llm_server.hardware_evidence.platform.machine", lambda: "arm64")
    monkeypatch.setattr("local_llm_server.hardware_evidence.platform.python_version", lambda: "3.12.5")

    payload = local_environment_metadata()

    assert payload == {
        "system": "darwin",
        "release": "25.6.0",
        "machine": "arm64",
        "python_version": "3.12.5",
    }
    assert "hostname" not in payload
    assert "node" not in payload


def test_hardware_report_persists_environment_without_prompt_or_private_path(monkeypatch):
    monkeypatch.setattr(
        "local_llm_server.hardware_evidence.local_environment_metadata",
        lambda: {
            "system": "linux",
            "release": "6.12.0",
            "machine": "x86_64",
            "python_version": "3.11.9",
        },
    )

    def config_builder(**kwargs):
        return {
            "model": "demo",
            "model_id": "org/demo",
            "model_path": "/private/models/demo.gguf",
            "backend": "fake",
            "modalities": ["text"],
            "default_temperature": 0.0,
            "default_top_p": 0.8,
            "default_top_k": 20,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "thinking_mode": "none",
            "force_json": False,
        }

    payload = execute_hardware_reclamation_evidence(
        HardwareEvidenceOptions(
            model="demo",
            prompt="PRIVATE PROMPT",
            settle_seconds=0,
        ),
        observer=WorkerSystemResourceObserver(_Observer()),
        config_builder=config_builder,
        experiment_runner=lambda *args, **kwargs: _Report(),
    )

    assert payload["environment"] == {
        "system": "linux",
        "release": "6.12.0",
        "machine": "x86_64",
        "python_version": "3.11.9",
    }
    rendered = json.dumps(payload)
    assert "PRIVATE PROMPT" not in rendered
    assert "/private/models" not in rendered
    assert "hostname" not in rendered.lower()
