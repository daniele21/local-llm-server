"""Representative worker lifecycle procedure for reclamation evidence.

This module binds the isolated batch worker adapter to the generic reclamation
harness. It records a bounded procedure descriptor alongside raw lifecycle
snapshots, but it never upgrades an observed memory delta into a PASS/FAIL claim.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .reclamation_experiment import ReclamationExperimentReport, run_reclamation_experiment
from .resources import ResourceObserver
from .runtime_identity import local_hardware_profile, resolved_config_digest
from .worker_engine import WorkerBackedEngine


WorkerFactory = Callable[[Mapping[str, Any]], WorkerBackedEngine]


@dataclass(frozen=True, slots=True)
class WorkerExperimentDescriptor:
    model_id: str
    backend: str
    backend_version: str | None
    artifact_sha256: str | None
    config_digest: str
    hardware: Mapping[str, object]
    procedure: str = "worker_reclamation_v1"
    execution_isolation: str = "subprocess_worker"
    streaming: bool = False

    @property
    def identity_grade(self) -> str:
        return (
            "verified"
            if self.artifact_sha256 is not None and self.backend_version is not None
            else "exploratory"
        )

    def to_public_dict(self) -> dict[str, object]:
        return {
            "procedure": self.procedure,
            "execution_isolation": self.execution_isolation,
            "streaming": self.streaming,
            "model_id": self.model_id,
            "backend": self.backend,
            "backend_version": self.backend_version,
            "artifact_sha256": self.artifact_sha256,
            "config_digest": self.config_digest,
            "hardware": dict(self.hardware),
            "identity_grade": self.identity_grade,
        }


@dataclass(frozen=True, slots=True)
class WorkerReclamationReport:
    descriptor: WorkerExperimentDescriptor
    experiment: ReclamationExperimentReport

    def to_public_dict(self) -> dict[str, object]:
        return {
            "descriptor": self.descriptor.to_public_dict(),
            "experiment": self.experiment.to_public_dict(),
            "claim_boundary": (
                "Observed lifecycle/resource evidence only. Representative repeated "
                "hardware evidence is required before claiming memory reclamation."
            ),
        }


def run_worker_reclamation_experiment(
    observer: ResourceObserver,
    *,
    config: Mapping[str, Any],
    request_payload: Mapping[str, Any],
    cycles: int,
    worker_factory: WorkerFactory = WorkerBackedEngine,
    settle_after_stop: Callable[[], None] | None = None,
) -> WorkerReclamationReport:
    """Run repeated load/complete/stop windows in isolated worker processes."""
    cfg = dict(config)
    payload = dict(request_payload)
    if payload.get("stream") is True:
        raise ValueError("worker reclamation procedure requires non-streaming workload")

    descriptor = _descriptor(cfg)

    def start() -> WorkerBackedEngine:
        return worker_factory(cfg)

    def wait_ready(worker: WorkerBackedEngine) -> None:
        health = worker.health()
        if health.get("accepted") is not True or health.get("prepared") is not True:
            raise RuntimeError("worker did not reach prepared ready state")

    def exercise(worker: WorkerBackedEngine) -> None:
        result = worker.complete(payload)
        if not isinstance(result, Mapping):
            raise RuntimeError("worker exercise returned an invalid result")

    def stop(worker: WorkerBackedEngine) -> None:
        worker.close()

    experiment = run_reclamation_experiment(
        observer,
        cycles=cycles,
        start=start,
        wait_ready=wait_ready,
        exercise=exercise,
        stop=stop,
        settle_after_stop=settle_after_stop,
    )
    return WorkerReclamationReport(descriptor=descriptor, experiment=experiment)


def _descriptor(config: Mapping[str, Any]) -> WorkerExperimentDescriptor:
    sha = config.get("artifact_sha256")
    artifact_sha256 = (
        str(sha).lower()
        if isinstance(sha, str) and len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha.lower())
        else None
    )
    backend_version = config.get("backend_version")
    version = (
        str(backend_version).strip()
        if isinstance(backend_version, str) and backend_version.strip()
        else None
    )
    hardware = local_hardware_profile(
        total_memory_bytes=(
            int(config["hardware_total_memory_bytes"])
            if isinstance(config.get("hardware_total_memory_bytes"), int)
            and not isinstance(config.get("hardware_total_memory_bytes"), bool)
            and int(config["hardware_total_memory_bytes"]) >= 0
            else None
        ),
        accelerator=(
            str(config["hardware_accelerator"])
            if config.get("hardware_accelerator") is not None
            else None
        ),
    )
    return WorkerExperimentDescriptor(
        model_id=str(config.get("model_id") or config.get("model") or "unknown"),
        backend=str(config.get("backend") or "unknown"),
        backend_version=version,
        artifact_sha256=artifact_sha256,
        config_digest=resolved_config_digest(config),
        hardware=hardware.stable_payload(),
    )
