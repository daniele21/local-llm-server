from __future__ import annotations

import pytest

from local_llm_server.residency_pressure import (
    PressureEvictionPolicy,
    PressurePolicySettings,
    PressurePolicyState,
)
from local_llm_server.resources import ResourcePressure


def _snapshot():
    return {
        "resident_default_model": "default",
        "runtimes": [
            {
                "key": "default",
                "model": "org/default",
                "evictable": True,
                "is_resident_default": True,
                "last_used_age_seconds": 90.0,
            },
            {
                "key": "old",
                "model": "org/old",
                "evictable": True,
                "is_resident_default": False,
                "last_used_age_seconds": 80.0,
            },
            {
                "key": "new",
                "model": "org/new",
                "evictable": True,
                "is_resident_default": False,
                "last_used_age_seconds": 10.0,
            },
            {
                "key": "pinned",
                "model": "org/pinned",
                "evictable": False,
                "is_resident_default": False,
                "last_used_age_seconds": 1000.0,
            },
        ],
    }


def test_policy_requires_consecutive_trigger_samples_and_protects_default():
    policy = PressureEvictionPolicy()

    first = policy.observe(ResourcePressure.CRITICAL, _snapshot())
    second = policy.observe(ResourcePressure.CRITICAL, _snapshot())

    assert first.state is PressurePolicyState.WATCHING
    assert first.should_attempt_eviction is False
    assert second.state is PressurePolicyState.TRIGGERED
    assert second.should_attempt_eviction is True
    assert [item.key for item in second.candidates] == ["old"]
    public = second.to_public_dict()
    assert public["automatic_eviction_enabled"] is False
    assert public["reclamation_claim"] is False


def test_triggered_episode_emits_only_one_attempt_until_cleared():
    policy = PressureEvictionPolicy()
    policy.observe(ResourcePressure.CRITICAL, _snapshot())
    triggered = policy.observe(ResourcePressure.CRITICAL, _snapshot())
    repeated = policy.observe(ResourcePressure.CRITICAL, _snapshot())
    one_clear = policy.observe(ResourcePressure.NORMAL, _snapshot())
    cleared = policy.observe(ResourcePressure.NORMAL, _snapshot())

    assert triggered.transition == "triggered"
    assert repeated.transition is None
    assert repeated.should_attempt_eviction is False
    assert one_clear.state is PressurePolicyState.TRIGGERED
    assert cleared.state is PressurePolicyState.NORMAL
    assert cleared.transition == "cleared"

    policy.observe(ResourcePressure.CRITICAL, _snapshot())
    retriggered = policy.observe(ResourcePressure.CRITICAL, _snapshot())
    assert retriggered.transition == "triggered"


def test_unknown_pressure_never_triggers_or_clears_existing_episode():
    policy = PressureEvictionPolicy()
    unknown = policy.observe(ResourcePressure.UNKNOWN, _snapshot())
    assert unknown.state is PressurePolicyState.NORMAL
    assert unknown.should_attempt_eviction is False

    policy.observe(ResourcePressure.CRITICAL, _snapshot())
    policy.observe(ResourcePressure.CRITICAL, _snapshot())
    unknown_while_triggered = policy.observe(ResourcePressure.UNKNOWN, _snapshot())
    assert unknown_while_triggered.state is PressurePolicyState.TRIGGERED
    assert unknown_while_triggered.transition is None


def test_elevated_does_not_trigger_default_critical_policy():
    policy = PressureEvictionPolicy()
    for _ in range(4):
        result = policy.observe(ResourcePressure.ELEVATED, _snapshot())
    assert result.state is PressurePolicyState.NORMAL
    assert result.should_attempt_eviction is False


def test_configurable_elevated_trigger_remains_hysteretic():
    policy = PressureEvictionPolicy(
        PressurePolicySettings(
            trigger_pressure=ResourcePressure.ELEVATED,
            consecutive_trigger_samples=3,
            clear_pressure=ResourcePressure.NORMAL,
            consecutive_clear_samples=1,
            candidate_limit=2,
        )
    )
    policy.observe(ResourcePressure.ELEVATED, _snapshot())
    policy.observe(ResourcePressure.ELEVATED, _snapshot())
    result = policy.observe(ResourcePressure.CRITICAL, _snapshot())

    assert result.should_attempt_eviction is True
    assert [item.key for item in result.candidates] == ["old", "new"]


def test_settings_reject_invalid_hysteresis_boundaries():
    with pytest.raises(ValueError):
        PressurePolicySettings(trigger_pressure=ResourcePressure.UNKNOWN)
    with pytest.raises(ValueError):
        PressurePolicySettings(clear_pressure=ResourcePressure.UNKNOWN)
    with pytest.raises(ValueError):
        PressurePolicySettings(
            trigger_pressure=ResourcePressure.ELEVATED,
            clear_pressure=ResourcePressure.ELEVATED,
        )
    with pytest.raises(ValueError):
        PressurePolicySettings(consecutive_trigger_samples=0)
    with pytest.raises(ValueError):
        PressurePolicySettings(consecutive_clear_samples=0)
    with pytest.raises(ValueError):
        PressurePolicySettings(candidate_limit=0)
