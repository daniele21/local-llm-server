from __future__ import annotations

import pytest

from local_llm_server.scheduler_policy import (
    RequestSchedulerSettings,
    scheduler_settings_from_env,
)


def test_scheduler_is_disabled_when_capacity_is_not_configured():
    settings = scheduler_settings_from_env({})
    assert settings.enabled is False
    assert settings.queue_capacity is None
    assert settings.default_queue_timeout_ms is None
    assert settings.to_public_dict()["timeout_scope"] == "queue_wait_only"


def test_scheduler_environment_configures_capacity_and_queue_only_timeout():
    settings = scheduler_settings_from_env(
        {
            "LOCAL_LLM_REQUEST_QUEUE_CAPACITY": "4",
            "LOCAL_LLM_QUEUE_TIMEOUT_MS": "250",
        }
    )
    assert settings.enabled is True
    assert settings.queue_capacity == 4
    assert settings.timeout_seconds_for_headers({}) == 0.25


def test_request_header_explicitly_overrides_default_queue_timeout():
    settings = RequestSchedulerSettings(queue_capacity=2, default_queue_timeout_ms=500)
    assert settings.timeout_seconds_for_headers(
        {"x-local-llm-queue-timeout-ms": "25"}
    ) == 0.025


def test_timeout_without_queue_capacity_is_rejected():
    with pytest.raises(ValueError, match="requires request queue capacity"):
        RequestSchedulerSettings(default_queue_timeout_ms=10)


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
