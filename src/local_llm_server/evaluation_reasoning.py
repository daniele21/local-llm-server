"""Stable reasoning policy for reproducible evaluation runs."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .core.capabilities import ThinkingMode, effective_thinking_mode


class EvaluationReasoningPolicy(str, Enum):
    OFF = "off"
    ON = "on"
    RUNTIME_DEFAULT = "runtime_default"


@dataclass(frozen=True, slots=True)
class EvaluationReasoningProfile:
    """Requested and effective thinking state for one evaluation run."""

    requested: EvaluationReasoningPolicy
    runtime_mode: ThinkingMode
    effective: str
    request_override: bool | None

    def __post_init__(self) -> None:
        if self.effective not in {"off", "on"}:
            raise ValueError("effective reasoning state must be 'off' or 'on'")

    def to_dict(self) -> dict[str, object]:
        return {
            "requested": self.requested.value,
            "runtime_mode": self.runtime_mode.value,
            "effective": self.effective,
            "request_override": self.request_override,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvaluationReasoningProfile":
        return cls(
            requested=EvaluationReasoningPolicy(str(value["requested"])),
            runtime_mode=ThinkingMode(str(value["runtime_mode"])),
            effective=str(value["effective"]),
            request_override=(
                None if value.get("request_override") is None
                else bool(value.get("request_override"))
            ),
        )


def resolve_evaluation_reasoning_profile(
    policy: EvaluationReasoningPolicy | str,
    runtime_config: Mapping[str, Any],
) -> EvaluationReasoningProfile:
    requested = (
        policy if isinstance(policy, EvaluationReasoningPolicy)
        else EvaluationReasoningPolicy(str(policy))
    )
    mode = effective_thinking_mode(runtime_config)
    configured = _configured_thinking(runtime_config)

    if mode is ThinkingMode.NONE:
        if requested is EvaluationReasoningPolicy.ON:
            raise ValueError("selected runtime cannot enable thinking for evaluation")
        return EvaluationReasoningProfile(
            requested=requested,
            runtime_mode=mode,
            effective="off",
            request_override=False if requested is EvaluationReasoningPolicy.OFF else None,
        )

    if mode is ThinkingMode.ALWAYS:
        # Preserve the user's requested policy in the manifest but never label
        # an always-thinking runtime as effectively OFF.
        return EvaluationReasoningProfile(
            requested=requested,
            runtime_mode=mode,
            effective="on",
            request_override=None,
        )

    if requested is EvaluationReasoningPolicy.OFF:
        return EvaluationReasoningProfile(
            requested=requested,
            runtime_mode=mode,
            effective="off",
            request_override=False,
        )
    if requested is EvaluationReasoningPolicy.ON:
        return EvaluationReasoningProfile(
            requested=requested,
            runtime_mode=mode,
            effective="on",
            request_override=True,
        )
    return EvaluationReasoningProfile(
        requested=requested,
        runtime_mode=mode,
        effective="on" if configured else "off",
        request_override=None,
    )


def default_reasoning_policy(test_set_id: str) -> EvaluationReasoningPolicy:
    # General-purpose objective quality must not silently pay for/benefit from
    # hidden reasoning. Other/custom contracts retain the runtime default until
    # they declare a stronger test-set-specific reasoning requirement.
    if test_set_id == "general-purpose":
        return EvaluationReasoningPolicy.OFF
    return EvaluationReasoningPolicy.RUNTIME_DEFAULT


def _configured_thinking(config: Mapping[str, Any]) -> bool:
    value = config.get("enable_thinking")
    if value is None:
        params = config.get("params")
        if isinstance(params, Mapping):
            value = params.get("enable_thinking")
    return bool(value)
