from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from local_llm_server.hardware_evidence import (
    HardwareEvidenceOptions,
    WorkerSystemResourceObserver,
    execute_hardware_reclamation_evidence,
    resolve_backend_version,
    write_evidence_report,
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
            process_rss_bytes=_measured(123456),
        )


class _Report:
    def to_public_dict(self):
        return {
            "descriptor": {
                "identity_grade": "verified",
                "config_digest": "a" * 64,
            },
            "experiment": {
                "cycle_count": 2,
                "interpretation": "Observational evidence only.",
            },
        }


def test_worker_system_observer_never_labels_parent_rss_as_worker_rss():
    snapshot = WorkerSystemResourceObserver(_Observer()).snapshot()

    assert snapshot.total_memory_bytes.value == 16 * 1024**3
    assert snapshot.available_memory_bytes.value == 8 * 1024**3
    assert snapshot.process_rss_bytes.value is None
    assert snapshot.process_rss_bytes.source is ResourceValueSource.UNAVAILABLE


def test_execute_hardware_evidence_uses_canonical_backend_request_and_omits_prompt_from_report():
    captured = {}

    def config_builder(**kwargs):
        captured["config_args"] = kwargs
        return {
            "model": "demo",
            "model_id": "org/demo",
            "model_path": "/private/models/demo.gguf",
            "backend": "llama_cpp",
            "modalities": ["text"],
            "artifact_sha256": "b" * 64,
            "default_temperature": 0.0,
            "default_top_p": 0.8,
            "default_top_k": 20,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "thinking_mode": "none",
            "force_json": False,
        }

    def runner(observer, **kwargs):
        captured["runner"] = kwargs
        return _Report()

    options = HardwareEvidenceOptions(
        model="demo",
        model_path="/private/models/demo.gguf",
        backend="llama_cpp",
        backend_version="0.3.99",
        accelerator="test-gpu",
        cycles=2,
        prompt="SUPER SECRET LOCAL PROMPT",
        max_tokens=17,
        settle_seconds=0,
        no_download=True,
    )

    payload = execute_hardware_reclamation_evidence(
        options,
        observer=WorkerSystemResourceObserver(_Observer()),
        config_builder=config_builder,
        experiment_runner=runner,
    )

    assert captured["config_args"] == {
        "model": "demo",
        "model_path": "/private/models/demo.gguf",
        "backend": "llama_cpp",
        "no_download": True,
    }
    runner_args = captured["runner"]
    assert runner_args["cycles"] == 2
    assert runner_args["config"]["backend_version"] == "0.3.99"
    assert runner_args["config"]["hardware_total_memory_bytes"] == 16 * 1024**3
    assert runner_args["config"]["hardware_accelerator"] == "test-gpu"
    assert runner_args["request_payload"]["messages"] == [
        {"role": "user", "content": "SUPER SECRET LOCAL PROMPT"}
    ]
    assert runner_args["request_payload"]["max_tokens"] == 17

    rendered = json.dumps(payload)
    assert "SUPER SECRET LOCAL PROMPT" not in rendered
    assert "/private/models" not in rendered
    assert payload["procedure"]["prompt_recorded"] is False
    assert payload["procedure"]["output_recorded"] is False
    assert payload["procedure"]["cycles"] == 2


def test_positive_settle_delay_is_executed_by_reclamation_callback():
    sleeps = []
    captured = {}

    def runner(observer, **kwargs):
        captured.update(kwargs)
        kwargs["settle_after_stop"]()
        return _Report()

    execute_hardware_reclamation_evidence(
        HardwareEvidenceOptions(model="demo", settle_seconds=1.25),
        observer=WorkerSystemResourceObserver(_Observer()),
        config_builder=lambda **kwargs: {
            "model": "demo",
            "model_id": "org/demo",
            "backend": "fake",
            "modalities": ["text"],
        },
        experiment_runner=runner,
        clock_sleep=sleeps.append,
    )

    assert sleeps == [1.25]
    assert callable(captured["settle_after_stop"])


def test_backend_version_prefers_explicit_then_installed_package(monkeypatch):
    assert resolve_backend_version(
        {"backend": "mlx", "backend_version": "explicit-1"}
    ) == "explicit-1"

    monkeypatch.setattr(
        "local_llm_server.hardware_evidence.metadata.version",
        lambda package: "0.31.7" if package == "mlx-lm" else "unexpected",
    )
    assert resolve_backend_version({"backend": "mlx"}) == "0.31.7"


def test_llama_server_version_probe_is_path_free(monkeypatch):
    monkeypatch.setattr(
        "local_llm_server.hardware_evidence.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="version: 9261 (`ad27757`)\nbuilt with compiler details\n",
            stderr="",
        ),
    )

    version = resolve_backend_version(
        {"backend": "llama_server", "llama_server_bin": "/private/bin/llama-server"}
    )

    assert version == "build-9261@ad27757"
    assert "/private" not in version


def test_atomic_report_writer_replaces_target_without_temp_residue(tmp_path: Path):
    path = tmp_path / "nested" / "evidence.json"
    write_evidence_report(path, {"schema_version": 1, "ok": True})

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "ok": True,
    }
    assert not path.with_suffix(".json.tmp").exists()


def test_options_reject_invalid_cycles_tokens_and_settle():
    with pytest.raises(ValueError):
        HardwareEvidenceOptions(model="")
    with pytest.raises(ValueError):
        HardwareEvidenceOptions(model="demo", cycles=0)
    with pytest.raises(ValueError):
        HardwareEvidenceOptions(model="demo", max_tokens=0)
    with pytest.raises(ValueError):
        HardwareEvidenceOptions(model="demo", settle_seconds=-1)


def test_cli_exposes_reclamation_command_without_embedding_prompt_in_report_contract():
    cli_path = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "cli.py"
    cli = cli_path.read_text(encoding="utf-8")

    assert '"evidence-reclamation"' in cli
    assert "HardwareEvidenceOptions" in cli
    assert "write_evidence_report" in cli
    assert "Prompt/output are not written to the evidence report" in cli
