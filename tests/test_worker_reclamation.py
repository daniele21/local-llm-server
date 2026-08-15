from __future__ import annotations

from collections import deque

import pytest

from local_llm_server.reclamation_evidence import RecoveryObservation
from local_llm_server.resources import ResourceValue, ResourceValueSource, SystemResourceSnapshot
from local_llm_server.worker_reclamation import run_worker_reclamation_experiment


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _snapshot(*, available: int, rss: int, clock: float) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=clock,
        platform="test",
        total_memory_bytes=_measured(2_000),
        available_memory_bytes=_measured(available),
        process_rss_bytes=_measured(rss),
    )


class _Observer:
    def __init__(self, snapshots):
        self.snapshots = deque(snapshots)

    def snapshot(self):
        return self.snapshots.popleft()


class _Worker:
    def __init__(self, events, *, ready=True, valid_result=True):
        self.events = events
        self.ready = ready
        self.valid_result = valid_result

    def health(self):
        self.events.append("health")
        return {"accepted": True, "prepared": self.ready, "state": "ready"}

    def complete(self, payload):
        self.events.append(("complete", dict(payload)))
        return {"choices": []} if self.valid_result else "invalid"

    def close(self):
        self.events.append("close")


def _config():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": "/private/models/demo.gguf",
        "backend": "mlx",
        "backend_version": "0.29.1",
        "artifact_sha256": "a" * 64,
        "ctx_size": 4096,
        "max_concurrent_requests": 1,
        "hardware_total_memory_bytes": 16 * 1024**3,
        "hardware_accelerator": "apple-gpu",
    }


def test_worker_reclamation_runs_repeated_ready_exercise_stop_windows():
    observer = _Observer(
        [
            _snapshot(available=1500, rss=100, clock=1),
            _snapshot(available=1100, rss=400, clock=2),
            _snapshot(available=1000, rss=500, clock=3),
            _snapshot(available=1450, rss=120, clock=4),
            _snapshot(available=1500, rss=100, clock=5),
            _snapshot(available=1120, rss=390, clock=6),
            _snapshot(available=1010, rss=490, clock=7),
            _snapshot(available=1440, rss=125, clock=8),
        ]
    )
    events = []

    report = run_worker_reclamation_experiment(
        observer,
        config=_config(),
        request_payload={"messages": [{"role": "user", "content": "hello"}]},
        cycles=2,
        worker_factory=lambda cfg: _Worker(events),
    )

    assert report.descriptor.identity_grade == "verified"
    assert report.descriptor.backend == "mlx"
    assert report.descriptor.artifact_sha256 == "a" * 64
    assert len(report.descriptor.config_digest) == 64
    assert report.descriptor.hardware["total_memory_bytes"] == 16 * 1024**3
    assert report.descriptor.hardware["accelerator"] == "apple-gpu"
    assert [cycle.evidence.observation for cycle in report.experiment.cycles] == [
        RecoveryObservation.RECOVERY_OBSERVED,
        RecoveryObservation.RECOVERY_OBSERVED,
    ]
    assert events == [
        "health",
        ("complete", {"messages": [{"role": "user", "content": "hello"}]}),
        "close",
        "health",
        ("complete", {"messages": [{"role": "user", "content": "hello"}]}),
        "close",
    ]

    public = report.to_public_dict()
    rendered = str(public)
    assert "/private/models" not in rendered
    assert "PASS" in public["experiment"]["interpretation"]
    assert "claim_boundary" in public


def test_missing_strong_identity_keeps_descriptor_exploratory():
    config = _config()
    config.pop("backend_version")
    config["artifact_sha256"] = "not-a-sha"
    observer = _Observer(
        [
            _snapshot(available=1500, rss=100, clock=1),
            _snapshot(available=1100, rss=400, clock=2),
            _snapshot(available=1000, rss=500, clock=3),
            _snapshot(available=1450, rss=120, clock=4),
        ]
    )

    report = run_worker_reclamation_experiment(
        observer,
        config=config,
        request_payload={"messages": []},
        cycles=1,
        worker_factory=lambda cfg: _Worker([]),
    )

    assert report.descriptor.identity_grade == "exploratory"
    assert report.descriptor.artifact_sha256 is None
    assert report.descriptor.backend_version is None


def test_non_streaming_procedure_rejects_stream_payload_before_start():
    observer = _Observer([])
    started = []

    with pytest.raises(ValueError, match="requires non-streaming workload"):
        run_worker_reclamation_experiment(
            observer,
            config=_config(),
            request_payload={"stream": True},
            cycles=1,
            worker_factory=lambda cfg: started.append(cfg),
        )

    assert started == []


def test_unready_worker_is_closed_and_cycle_is_error_not_false_success():
    observer = _Observer(
        [
            _snapshot(available=1500, rss=100, clock=1),
            _snapshot(available=1450, rss=120, clock=2),
        ]
    )
    events = []

    report = run_worker_reclamation_experiment(
        observer,
        config=_config(),
        request_payload={"messages": []},
        cycles=1,
        worker_factory=lambda cfg: _Worker(events, ready=False),
    )

    cycle = report.experiment.cycles[0]
    assert cycle.completed_without_error is False
    assert cycle.error_stage.value == "ready"
    assert events == ["health", "close"]
    assert cycle.evidence.complete_window is False


def test_invalid_completed_result_is_exercise_error_and_worker_still_closes():
    observer = _Observer(
        [
            _snapshot(available=1500, rss=100, clock=1),
            _snapshot(available=1100, rss=400, clock=2),
            _snapshot(available=1450, rss=120, clock=3),
        ]
    )
    events = []

    report = run_worker_reclamation_experiment(
        observer,
        config=_config(),
        request_payload={"messages": []},
        cycles=1,
        worker_factory=lambda cfg: _Worker(events, valid_result=False),
    )

    cycle = report.experiment.cycles[0]
    assert cycle.error_stage.value == "exercise"
    assert events == ["health", ("complete", {"messages": []}), "close"]
