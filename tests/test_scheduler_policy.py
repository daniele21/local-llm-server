from __future__ import annotations

import pytest

from local_llm_server.scheduler_policy import (
    RequestSchedulerSettings,
    scheduler_settings_from_env,
)


def test_scheduler_is_disabled_when_no_admission_policy_is_configured():
    settings = scheduler_settings_from_env({})
    assert settings.enabled is False
    assert settings.runtime_queue_enabled is False
    assert settings.global_governor_enabled is False
    assert settings.queue_capacity is None
    assert settings.global_max_running is None
    assert settings.global_queue_capacity is None
    assert settings.default_queue_timeout_ms is None
    assert settings.to_public_dict()["timeout_scope"] == "pre_execution_admission_wait_only"


def test_scheduler_environment_configures_runtime_queue_and_timeout():
    settings = scheduler_settings_from_env(
        {
            "LOCAL_LLM_REQUEST_QUEUE_CAPACITY": "4",
            "LOCAL_LLM_QUEUE_TIMEOUT_MS": "250",
        }
    )
    assert settings.enabled is True
    assert settings.runtime_queue_enabled is True
    assert settings.global_governor_enabled is False
    assert settings.queue_capacity == 4
    assert settings.timeout_seconds_for_headers({}) == 0.25


def test_environment_can_enable_global_governor_without_runtime_queue():
    settings = scheduler_settings_from_env(
        {
            "LOCAL_LLM_GLOBAL_MAX_RUNNING": "2",
            "LOCAL_LLM_GLOBAL_QUEUE_CAPACITY": "5",
            "LOCAL_LLM_QUEUE_TIMEOUT_MS": "300",
        }
    )
    assert settings.enabled is True
    assert settings.runtime_queue_enabled is False
    assert settings.global_governor_enabled is True
    assert settings.global_max_running == 2
    assert settings.global_queue_capacity == 5
    assert settings.timeout_seconds_for_headers({}) == 0.3
    public = settings.to_public_dict()
    assert public["global_fairness"] == "runtime_round_robin"


def test_request_header_explicitly_overrides_default_admission_timeout():
    settings = RequestSchedulerSettings(
        global_max_running=2,
        global_queue_capacity=4,
        default_queue_timeout_ms=500,
    )
    assert settings.timeout_seconds_for_headers(
        {"x-local-llm-queue-timeout-ms": "25"}
    ) == 0.025


def test_timeout_without_any_admission_policy_is_rejected():
    with pytest.raises(ValueError, match="requires request queue capacity or global"):
        RequestSchedulerSettings(default_queue_timeout_ms=10)


def test_partial_global_governor_configuration_is_rejected():
    with pytest.raises(ValueError, match="requires both"):
        RequestSchedulerSettings(global_max_running=2)
    with pytest.raises(ValueError, match="requires both"):
        RequestSchedulerSettings(global_queue_capacity=2)


def test_invalid_timeout_header_is_rejected_instead_of_becoming_no_timeout():
    settings = RequestSchedulerSettings(queue_capacity=2)
    with pytest.raises(ValueError, match="positive integer"):
        settings.timeout_seconds_for_headers(
            {"x-local-llm-queue-timeout-ms": "soon"}
        )
    with pytest.raises(ValueError, match=">= 1"):
        settings.timeout_seconds_for_headers(
            {"x-local-llm-queue-timeout-ms": "0"}
        )
