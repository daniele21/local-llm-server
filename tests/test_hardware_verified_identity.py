from __future__ import annotations

from collections import deque

from local_llm_server.artifact_identity import ArtifactVerificationReceipt, sha256_file
from local_llm_server.artifact_verification import ArtifactVerificationStore
from local_llm_server.hardware_evidence import (
    HardwareEvidenceOptions,
    execute_hardware_reclamation_evidence,
)
from local_llm_server.resources import ResourceValue, ResourceValueSource, SystemResourceSnapshot
from local_llm_server.worker_reclamation import run_worker_reclamation_experiment


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _snapshot(clock: float, available: int, rss: int) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=clock,
        platform="test",
        total_memory_bytes=_measured(16 * 1024**3),
        available_memory_bytes=_measured(available),
        process_rss_bytes=_measured(rss),
    )


class _Observer:
    def __init__(self):
        # One preflight snapshot plus four snapshots for one complete lifecycle cycle.
        self.snapshots = deque(
            [
                _snapshot(0, 8_000, 0),
                _snapshot(1, 7_000, 0),
                _snapshot(2, 6_000, 400),
                _snapshot(3, 5_500, 500),
                _snapshot(4, 6_900, 0),
            ]
        )

    def snapshot(self):
        return self.snapshots.popleft()


class _Worker:
    def health(self):
        return {"accepted": True, "prepared": True, "state": "ready"}

    def complete(self, payload):
        return {"choices": [{"message": {"content": "OK"}}]}

    def close(self):
        pass


def _runner(observer, **kwargs):
    return run_worker_reclamation_experiment(
        observer,
        worker_factory=lambda cfg: _Worker(),
        **kwargs,
    )


def test_verified_receipt_promotes_exact_hardware_descriptor_without_rehash(tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"representative-model")
    digest = sha256_file(artifact)
    store = ArtifactVerificationStore(tmp_path / "receipts")
    store.save(
        ArtifactVerificationReceipt.for_file(
            "org/demo",
            artifact,
            sha256=digest,
        )
    )

    def config_builder(**kwargs):
        return {
            "model": "demo",
            "model_id": "org/demo",
            "model_path": str(artifact),
            "model_source": "explicit",
            "backend": "fake",
            "modalities": ["text"],
            "default_temperature": 0.0,
            "default_top_p": 1.0,
            "default_top_k": 40,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "thinking_mode": "none",
            "enable_thinking": False,
            "force_json": False,
            "ctx_size": 4096,
            "max_concurrent_requests": 1,
        }

    payload = execute_hardware_reclamation_evidence(
        HardwareEvidenceOptions(
            model="demo",
            cycles=1,
            max_tokens=4,
            backend_version="fake-1.0",
            settle_seconds=0,
        ),
        observer=_Observer(),
        config_builder=config_builder,
        experiment_runner=_runner,
        verification_store=store,
    )

    descriptor = payload["report"]["descriptor"]
    assert descriptor["identity_grade"] == "verified"
    assert descriptor["artifact_sha256"] == digest
    assert descriptor["backend_version"] == "fake-1.0"
    assert str(tmp_path) not in str(payload)


def test_stale_receipt_keeps_hardware_descriptor_exploratory(tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"first-model")
    store = ArtifactVerificationStore(tmp_path / "receipts")
    store.save(
        ArtifactVerificationReceipt.for_file(
            "org/demo",
            artifact,
            sha256=sha256_file(artifact),
        )
    )
    artifact.write_bytes(b"changed-model-longer")

    def config_builder(**kwargs):
        return {
            "model": "demo",
            "model_id": "org/demo",
            "model_path": str(artifact),
            "backend": "fake",
            "modalities": ["text"],
            "default_temperature": 0.0,
            "default_top_p": 1.0,
            "default_top_k": 40,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "thinking_mode": "none",
            "force_json": False,
            "ctx_size": 4096,
            "max_concurrent_requests": 1,
        }

    payload = execute_hardware_reclamation_evidence(
        HardwareEvidenceOptions(
            model="demo",
            cycles=1,
            max_tokens=4,
            backend_version="fake-1.0",
            settle_seconds=0,
        ),
        observer=_Observer(),
        config_builder=config_builder,
        experiment_runner=_runner,
        verification_store=store,
    )

    descriptor = payload["report"]["descriptor"]
    assert descriptor["identity_grade"] == "exploratory"
    assert descriptor["artifact_sha256"] is None
