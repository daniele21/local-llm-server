"""Resource evidence across a runtime/worker lifecycle.

The recorder preserves raw snapshots and derives bounded deltas only when both
endpoints are measured. A positive delta is recorded as recovery *observed*;
it is deliberately not promoted to PASS or a general reclaimability claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .resources import ResourceObserver, ResourceValue, ResourceValueSource, SystemResourceSnapshot


class EvidenceStage(str, Enum):
    BEFORE_START = "before_start"
    AFTER_READY = "after_ready"
    PEAK = "peak"
    AFTER_STOP = "after_stop"


class RecoveryObservation(str, Enum):
    INCONCLUSIVE = "inconclusive"
    RECOVERY_OBSERVED = "recovery_observed"
    NO_RECOVERY_OBSERVED = "no_recovery_observed"


@dataclass(frozen=True, slots=True)
class ReclamationEvidence:
    snapshots: Mapping[EvidenceStage, SystemResourceSnapshot]
    ready_to_stop_rss_delta_bytes: int | None
    ready_to_stop_available_gain_bytes: int | None
    peak_to_stop_rss_delta_bytes: int | None
    observation: RecoveryObservation

    @property
    def complete_window(self) -> bool:
        return (
            EvidenceStage.BEFORE_START in self.snapshots
            and EvidenceStage.AFTER_READY in self.snapshots
            and EvidenceStage.AFTER_STOP in self.snapshots
        )

    def to_public_dict(self) -> dict[str, object]:
        return {
            "stages": {
                stage.value: _snapshot_to_dict(snapshot)
                for stage, snapshot in sorted(self.snapshots.items(), key=lambda item: item[0].value)
            },
            "ready_to_stop_rss_delta_bytes": self.ready_to_stop_rss_delta_bytes,
            "ready_to_stop_available_gain_bytes": self.ready_to_stop_available_gain_bytes,
            "peak_to_stop_rss_delta_bytes": self.peak_to_stop_rss_delta_bytes,
            "observation": self.observation.value,
            "complete_window": self.complete_window,
        }


class ReclamationEvidenceRecorder:
    def __init__(self, observer: ResourceObserver) -> None:
        self.observer = observer
        self._snapshots: dict[EvidenceStage, SystemResourceSnapshot] = {}

    def capture(self, stage: EvidenceStage) -> SystemResourceSnapshot:
        snapshot = self.observer.snapshot()
        self._snapshots[stage] = snapshot
        return snapshot

    def build(self) -> ReclamationEvidence:
        snapshots = dict(self._snapshots)
        ready = snapshots.get(EvidenceStage.AFTER_READY)
        peak = snapshots.get(EvidenceStage.PEAK)
        stopped = snapshots.get(EvidenceStage.AFTER_STOP)

        ready_rss_delta = _decrease(
            ready.process_rss_bytes if ready else None,
            stopped.process_rss_bytes if stopped else None,
        )
        peak_rss_delta = _decrease(
            peak.process_rss_bytes if peak else None,
            stopped.process_rss_bytes if stopped else None,
        )
        available_gain = _increase(
            ready.available_memory_bytes if ready else None,
            stopped.available_memory_bytes if stopped else None,
        )

        observation = RecoveryObservation.INCONCLUSIVE
        comparable = [value for value in (ready_rss_delta, peak_rss_delta, available_gain) if value is not None]
        if comparable:
            observation = (
                RecoveryObservation.RECOVERY_OBSERVED
                if any(value > 0 for value in comparable)
                else RecoveryObservation.NO_RECOVERY_OBSERVED
            )

        return ReclamationEvidence(
            snapshots=snapshots,
            ready_to_stop_rss_delta_bytes=ready_rss_delta,
            ready_to_stop_available_gain_bytes=available_gain,
            peak_to_stop_rss_delta_bytes=peak_rss_delta,
            observation=observation,
        )


def _decrease(before: ResourceValue | None, after: ResourceValue | None) -> int | None:
    pair = _measured_pair(before, after)
    if pair is None:
        return None
    first, second = pair
    return int(first - second)


def _increase(before: ResourceValue | None, after: ResourceValue | None) -> int | None:
    pair = _measured_pair(before, after)
    if pair is None:
        return None
    first, second = pair
    return int(second - first)


def _measured_pair(
    first: ResourceValue | None,
    second: ResourceValue | None,
) -> tuple[float, float] | None:
    if first is None or second is None:
        return None
    if first.source is not ResourceValueSource.MEASURED or second.source is not ResourceValueSource.MEASURED:
        return None
    if first.unit != second.unit or first.unit != "bytes":
        return None
    if not isinstance(first.value, (int, float)) or not isinstance(second.value, (int, float)):
        return None
    return float(first.value), float(second.value)


def _resource_value_to_dict(value: ResourceValue) -> dict[str, object]:
    return {"value": value.value, "source": value.source.value, "unit": value.unit}


def _snapshot_to_dict(snapshot: SystemResourceSnapshot) -> dict[str, object]:
    return {
        "captured_at_monotonic": snapshot.captured_at_monotonic,
        "platform": snapshot.platform,
        "total_memory_bytes": _resource_value_to_dict(snapshot.total_memory_bytes),
        "available_memory_bytes": _resource_value_to_dict(snapshot.available_memory_bytes),
        "process_rss_bytes": _resource_value_to_dict(snapshot.process_rss_bytes),
        "accelerator_memory_bytes": _resource_value_to_dict(snapshot.accelerator_memory_bytes),
        "thermal_pressure": _resource_value_to_dict(snapshot.thermal_pressure),
    }
