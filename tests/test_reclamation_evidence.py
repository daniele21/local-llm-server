from __future__ import annotations

from local_llm_server.reclamation_evidence import (
    EvidenceStage,
    ReclamationEvidenceRecorder,
    RecoveryObservation,
)
from local_llm_server.resources import (
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
)


def _measured(value: int) -> ResourceValue:
    return ResourceValue(value, ResourceValueSource.MEASURED, "bytes")


def _snapshot(t: float, *, rss: int | None, available: int | None) -> SystemResourceSnapshot:
    return SystemResourceSnapshot(
        captured_at_monotonic=t,
        platform="test",
        total_memory_bytes=_measured(10_000),
        available_memory_bytes=(
            _measured(available) if available is not None else ResourceValue.unavailable("bytes")
        ),
        process_rss_bytes=(
            _measured(rss) if rss is not None else ResourceValue.unavailable("bytes")
        ),
    )


class _Observer:
    def __init__(self, snapshots):
        self.snapshots = iter(snapshots)

    def snapshot(self):
        return next(self.snapshots)


def test_complete_window_records_observed_recovery_without_pass_label():
    recorder = ReclamationEvidenceRecorder(
        _Observer(
            [
                _snapshot(1, rss=100, available=5_000),
                _snapshot(2, rss=600, available=4_400),
                _snapshot(3, rss=800, available=4_200),
                _snapshot(4, rss=150, available=4_950),
            ]
        )
    )
    recorder.capture(EvidenceStage.BEFORE_START)
    recorder.capture(EvidenceStage.AFTER_READY)
    recorder.capture(EvidenceStage.PEAK)
    recorder.capture(EvidenceStage.AFTER_STOP)

    evidence = recorder.build()

    assert evidence.complete_window is True
    assert evidence.ready_to_stop_rss_delta_bytes == 450
    assert evidence.peak_to_stop_rss_delta_bytes == 650
    assert evidence.ready_to_stop_available_gain_bytes == 550
    assert evidence.observation is RecoveryObservation.RECOVERY_OBSERVED
    assert "pass" not in evidence.to_public_dict()


def test_missing_measured_values_remain_inconclusive():
    recorder = ReclamationEvidenceRecorder(
        _Observer(
            [
                _snapshot(1, rss=None, available=None),
                _snapshot(2, rss=None, available=None),
                _snapshot(3, rss=None, available=None),
            ]
        )
    )
    recorder.capture(EvidenceStage.BEFORE_START)
    recorder.capture(EvidenceStage.AFTER_READY)
    recorder.capture(EvidenceStage.AFTER_STOP)

    evidence = recorder.build()

    assert evidence.complete_window is True
    assert evidence.ready_to_stop_rss_delta_bytes is None
    assert evidence.ready_to_stop_available_gain_bytes is None
    assert evidence.observation is RecoveryObservation.INCONCLUSIVE


def test_no_positive_delta_is_recorded_as_no_recovery_observed_not_failure():
    recorder = ReclamationEvidenceRecorder(
        _Observer(
            [
                _snapshot(1, rss=500, available=4_000),
                _snapshot(2, rss=500, available=4_000),
                _snapshot(3, rss=550, available=3_950),
            ]
        )
    )
    recorder.capture(EvidenceStage.BEFORE_START)
    recorder.capture(EvidenceStage.AFTER_READY)
    recorder.capture(EvidenceStage.AFTER_STOP)

    evidence = recorder.build()

    assert evidence.ready_to_stop_rss_delta_bytes == -50
    assert evidence.ready_to_stop_available_gain_bytes == -50
    assert evidence.observation is RecoveryObservation.NO_RECOVERY_OBSERVED


def test_estimated_values_are_not_compared_as_measured_evidence():
    estimated = ResourceValue(500, ResourceValueSource.ESTIMATED, "bytes")
    stopped = _snapshot(2, rss=100, available=5_000)
    ready = SystemResourceSnapshot(
        captured_at_monotonic=1,
        platform="test",
        total_memory_bytes=_measured(10_000),
        available_memory_bytes=_measured(4_000),
        process_rss_bytes=estimated,
    )
    recorder = ReclamationEvidenceRecorder(_Observer([ready, stopped]))
    recorder.capture(EvidenceStage.AFTER_READY)
    recorder.capture(EvidenceStage.AFTER_STOP)

    evidence = recorder.build()
    assert evidence.ready_to_stop_rss_delta_bytes is None
