from __future__ import annotations

import pytest

from local_llm_server.resources import (
    ResourceBudget,
    ResourcePressure,
    ResourceValue,
    ResourceValueSource,
    RuntimeResourceProfile,
    SystemResourceSnapshot,
    classify_memory_pressure,
)


def _snapshot(total, available):
    return SystemResourceSnapshot(
        captured_at_monotonic=1.0,
        platform="test",
        total_memory_bytes=total,
        available_memory_bytes=available,
    )


def test_unavailable_value_never_uses_fake_zero():
    value = ResourceValue.unavailable("bytes")
    assert value.value is None
    assert value.available is False
    assert value.source is ResourceValueSource.UNAVAILABLE


def test_invalid_unavailable_value_is_rejected():
    with pytest.raises(ValueError):
        ResourceValue(0, ResourceValueSource.UNAVAILABLE, "bytes")


def test_budget_preserves_headroom():
    budget = ResourceBudget(limit_bytes=10_000, headroom_bytes=2_000)
    assert budget.usable_bytes == 8_000


def test_unbounded_budget_stays_explicitly_unbounded():
    assert ResourceBudget(limit_bytes=None, headroom_bytes=1_000).usable_bytes is None


def test_pressure_classification_uses_measured_fraction():
    total = ResourceValue(100, ResourceValueSource.MEASURED, "bytes")
    assert classify_memory_pressure(_snapshot(total, ResourceValue(50, ResourceValueSource.MEASURED, "bytes"))) is ResourcePressure.NORMAL
    assert classify_memory_pressure(_snapshot(total, ResourceValue(20, ResourceValueSource.MEASURED, "bytes"))) is ResourcePressure.ELEVATED
    assert classify_memory_pressure(_snapshot(total, ResourceValue(10, ResourceValueSource.MEASURED, "bytes"))) is ResourcePressure.CRITICAL


def test_pressure_is_unknown_when_measurement_is_unavailable():
    snapshot = _snapshot(ResourceValue.unavailable("bytes"), ResourceValue.unavailable("bytes"))
    assert classify_memory_pressure(snapshot) is ResourcePressure.UNKNOWN


def test_runtime_profile_distinguishes_estimate_and_observation():
    profile = RuntimeResourceProfile(
        runtime_id="model-a",
        estimated_resident_bytes=ResourceValue(4_000, ResourceValueSource.ESTIMATED, "bytes"),
        observed_resident_bytes=ResourceValue(4_500, ResourceValueSource.MEASURED, "bytes"),
    )
    assert profile.estimated_resident_bytes.source is ResourceValueSource.ESTIMATED
    assert profile.observed_resident_bytes.source is ResourceValueSource.MEASURED
