from __future__ import annotations

import pytest

from local_llm_server.core.contracts import ErrorCode, InferenceError, OutputConstraints
from local_llm_server.structured_output import parse_structured_output


def test_json_object_success_means_complete_content_is_parseable_object():
    parsed = parse_structured_output(
        '{"answer": 42, "ok": true}',
        OutputConstraints(format="json_object"),
    )

    assert parsed == {"answer": 42, "ok": True}


def test_json_schema_uses_same_application_json_boundary():
    parsed = parse_structured_output(
        '{"name": "Ada"}',
        OutputConstraints(
            format="json_schema",
            json_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        ),
    )

    assert parsed == {"name": "Ada"}


def test_reasoning_prefix_is_not_silently_stripped_or_repaired():
    with pytest.raises(InferenceError) as exc_info:
        parse_structured_output(
            'I should reason first.\n{"answer": 42}',
            OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_think_block_mixed_with_json_is_invalid_at_application_boundary():
    with pytest.raises(InferenceError) as exc_info:
        parse_structured_output(
            '<think>private reasoning</think>{"answer": 42}',
            OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_markdown_fence_is_not_treated_as_valid_json():
    with pytest.raises(InferenceError) as exc_info:
        parse_structured_output(
            '```json\n{"answer": 42}\n```',
            OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_non_object_json_is_invalid_for_json_object_contract():
    with pytest.raises(InferenceError) as exc_info:
        parse_structured_output(
            '[1, 2, 3]',
            OutputConstraints(format="json_object"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_MODEL_OUTPUT


def test_no_constraint_does_not_parse_or_modify_content():
    assert parse_structured_output("not-json", OutputConstraints()) is None


def test_unknown_structured_format_is_an_invalid_request_not_model_failure():
    with pytest.raises(InferenceError) as exc_info:
        parse_structured_output(
            '{"answer": 42}',
            OutputConstraints(format="yaml"),
        )

    assert exc_info.value.code is ErrorCode.INVALID_REQUEST
