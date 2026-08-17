from __future__ import annotations

import pytest

from local_llm_server.evaluation_reasoning import (
    EvaluationReasoningPolicy,
    default_reasoning_policy,
    resolve_evaluation_reasoning_profile,
)


def test_general_purpose_defaults_to_explicit_reasoning_off():
    assert default_reasoning_policy("general-purpose") is EvaluationReasoningPolicy.OFF
    assert default_reasoning_policy("custom-quality") is EvaluationReasoningPolicy.RUNTIME_DEFAULT


def test_switchable_off_is_recorded_and_sent_as_explicit_false():
    profile = resolve_evaluation_reasoning_profile(
        EvaluationReasoningPolicy.OFF,
        {
            "backend": "llama_cpp",
            "thinking_mode": "switchable",
            "enable_thinking": True,
        },
    )

    assert profile.to_dict() == {
        "requested": "off",
        "runtime_mode": "switchable",
        "effective": "off",
        "request_override": False,
    }


def test_switchable_runtime_default_records_actual_configured_state_without_override():
    on = resolve_evaluation_reasoning_profile(
        "runtime_default",
        {
            "backend": "llama_cpp",
            "thinking_mode": "switchable",
            "enable_thinking": True,
        },
    )
    off = resolve_evaluation_reasoning_profile(
        "runtime_default",
        {
            "backend": "llama_cpp",
            "thinking_mode": "switchable",
            "enable_thinking": False,
        },
    )

    assert on.effective == "on"
    assert on.request_override is None
    assert off.effective == "off"
    assert off.request_override is None


def test_always_runtime_never_claims_effective_off():
    profile = resolve_evaluation_reasoning_profile(
        EvaluationReasoningPolicy.OFF,
        {"thinking_mode": "always", "backend": "llama_cpp"},
    )

    assert profile.requested is EvaluationReasoningPolicy.OFF
    assert profile.runtime_mode.value == "always"
    assert profile.effective == "on"
    assert profile.request_override is None


def test_none_runtime_rejects_requested_on():
    with pytest.raises(ValueError, match="cannot enable thinking"):
        resolve_evaluation_reasoning_profile(
            "on",
            {"thinking_mode": "none", "backend": "llama_cpp"},
        )


def test_policy_enum_string_coercion_is_stable_for_api_and_internal_callers():
    assert str(EvaluationReasoningPolicy.OFF) == "off"
    profile = resolve_evaluation_reasoning_profile(
        EvaluationReasoningPolicy.ON,
        {"thinking_mode": "switchable", "backend": "llama_cpp"},
    )
    assert profile.requested is EvaluationReasoningPolicy.ON
    assert profile.request_override is True
