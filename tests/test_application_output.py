from __future__ import annotations

import pytest

from local_llm_server.application_output import (
    normalize_application_output,
    request_expects_reasoning,
)
from local_llm_server.core.contracts import ErrorCode, InferenceError, OutputConstraints


def test_reasoning_is_separated_before_strict_json_validation():
    normalized = normalize_application_output(
        'private chain</think>{"answer":42}',
        expect_reasoning=True,
        constraints=OutputConstraints(format="json_object"),
    )

    assert normalized.reasoning == "private chain"
    assert normalized.final_content == '{"answer":42}'
    assert normalized.structured_output == {"answer": 42}


def test_clean_no_thinking_json_is_unchanged():
    normalized = normalize_application_output(
        '{"answer":42}',
        expect_reasoning=False,
        constraints=OutputConstraints(format="json_object"),
    )

    assert normalized.reasoning == ""
    assert normalized.final_content == '{"answer":42}'
    assert normalized.structured_output == {"answer": 42}


def test_malformed_final_json_is_a_model_output_failure_not_repaired():
    with pytest.raises(InferenceError) as exc_info:
        normalize_application_output(
            'reason</think>{"answer":42',
            expect_reasoning=True,
            constraints=OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_reasoning_prefix_without_close_fails_closed_instead_of_becoming_json():
    with pytest.raises(InferenceError) as exc_info:
        normalize_application_output(
            'private reasoning {"answer":42}',
            expect_reasoning=True,
            constraints=OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_effective_request_reasoning_matches_runtime_contract():
    assert request_expects_reasoning(
        False,
        {"backend": "llama_cpp", "thinking_mode": "switchable", "enable_thinking": True},
    ) is False
    assert request_expects_reasoning(
        None,
        {"backend": "llama_cpp", "thinking_mode": "switchable", "enable_thinking": True},
    ) is True
    assert request_expects_reasoning(
        False,
        {"backend": "llama_cpp", "thinking_mode": "always"},
    ) is True
    assert request_expects_reasoning(
        True,
        {"backend": "llama_cpp", "thinking_mode": "none"},
    ) is False
