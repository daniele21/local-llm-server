"""Explicit product settings for request queue and global execution admission.

Queueing remains opt-in. A configured timeout applies only while waiting for
pre-execution admission (per-runtime queue and/or global governor); it is not
presented as an end-to-end inference deadline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

_QUEUE_CAPACITY_ENV = "LOCAL_LLM_REQUEST_QUEUE_CAPACITY"
_QUEUE_TIMEOUT_ENV = "LOCAL_LLM_QUEUE_TIMEOUT_MS"
_QUEUE_TIMEOUT_HEADER = "x-local-llm-queue-timeout-ms"
_GLOBAL_MAX_RUNNING_ENV = "LOCAL_LLM_GLOBAL_MAX_RUNNING"
_GLOBAL_QUEUE_CAPACITY_ENV = "LOCAL_LLM_GLOBAL_QUEUE_CAPACITY"


@dataclass(frozen=True, slots=True)
class RequestSchedulerSettings:
    queue_capacity: int | None = None
    default_queue_timeout_ms: int | None = None
    global_max_running: int | None = None
    global_queue_capacity: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("queue_capacity", self.queue_capacity),
            ("default_queue_timeout_ms", self.default_queue_timeout_ms),
            ("global_max_running", self.global_max_running),
            ("global_queue_capacity", self.global_queue_capacity),
        ):
            if value is not None and value < 1:
                raise ValueError(f"{name} must be >= 1")
        if (self.global_max_running is None) != (self.global_queue_capacity is None):
            raise ValueError(
                "global execution governor requires both global_max_running and "
                "global_queue_capacity"
            )
        if self.default_queue_timeout_ms is not None and not self.enabled:
            raise ValueError(
                "queue timeout requires request queue capacity or global execution governor"
            )

    @property
    def runtime_queue_enabled(self) -> bool:
        return self.queue_capacity is not None

    @property
    def global_governor_enabled(self) -> bool:
        return self.global_max_running is not None and self.global_queue_capacity is not None

    @property
    def enabled(self) -> bool:
        return self.runtime_queue_enabled or self.global_governor_enabled

    def timeout_seconds_for_headers(self, headers: Mapping[str, str]) -> float | None:
        raw = headers.get(_QUEUE_TIMEOUT_HEADER)
        if raw is not None:
            try:
                milliseconds = int(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{_QUEUE_TIMEOUT_HEADER} must be a positive integer") from exc
            if milliseconds < 1:
                raise ValueError(f"{_QUEUE_TIMEOUT_HEADER} must be >= 1")
            return milliseconds / 1000.0
        if self.default_queue_timeout_ms is None:
            return None
        return self.default_queue_timeout_ms / 1000.0

    def to_public_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "runtime_queue_enabled": self.runtime_queue_enabled,
            "queue_capacity": self.queue_capacity,
            "global_governor_enabled": self.global_governor_enabled,
            "global_max_running": self.global_max_running,
            "global_queue_capacity": self.global_queue_capacity,
            "global_fairness": (
                "runtime_round_robin" if self.global_governor_enabled else None
            ),
            "default_queue_timeout_ms": self.default_queue_timeout_ms,
            "request_timeout_header": _QUEUE_TIMEOUT_HEADER,
            "timeout_scope": "pre_execution_admission_wait_only",
        }


def scheduler_settings_from_env(
    env: Mapping[str, str] | None = None,
) -> RequestSchedulerSettings:
    source = os.environ if env is None else env
    return RequestSchedulerSettings(
        queue_capacity=_optional_positive_int(source.get(_QUEUE_CAPACITY_ENV), _QUEUE_CAPACITY_ENV),
        default_queue_timeout_ms=_optional_positive_int(
            source.get(_QUEUE_TIMEOUT_ENV), _QUEUE_TIMEOUT_ENV
        ),
        global_max_running=_optional_positive_int(
            source.get(_GLOBAL_MAX_RUNNING_ENV), _GLOBAL_MAX_RUNNING_ENV
        ),
        global_queue_capacity=_optional_positive_int(
            source.get(_GLOBAL_QUEUE_CAPACITY_ENV), _GLOBAL_QUEUE_CAPACITY_ENV
        ),
    )


def _optional_positive_int(value: str | None, name: str) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be >= 1")
    return parsed
