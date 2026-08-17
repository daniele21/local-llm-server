"""Strict application-level structured-output validation.

The contract in this module intentionally validates only the final application
answer. It never extracts a JSON-looking substring, strips reasoning text, or
repairs malformed model output. Reasoning separation belongs to the response
parser; once content reaches this boundary it must already be the final answer.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .core.contracts import ErrorCode, InferenceError, OutputConstraints

_JSON_OBJECT_FORMATS = frozenset({"json_object", "json_schema"})


def parse_structured_output(
    content: str,
    constraints: OutputConstraints,
) -> Mapping[str, Any] | None:
    """Parse a final application answer under the canonical JSON contract.

    A successful ``json_object``/``json_schema`` completion means the complete
    final content is a JSON object. Prefix/suffix prose, reasoning blocks,
    Markdown fences and malformed JSON are model-output failures, not inputs to
    a best-effort repair path.
    """
    if constraints.format is None:
        return None
    if constraints.format not in _JSON_OBJECT_FORMATS:
        raise InferenceError(
            ErrorCode.INVALID_REQUEST,
            "Unsupported structured output format.",
            retryable=False,
            details={"format": constraints.format},
        )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise InferenceError(
            ErrorCode.INVALID_MODEL_OUTPUT,
            "Model returned invalid JSON for the requested structured output.",
            retryable=False,
            details={
                "format": constraints.format,
                "line": exc.lineno,
                "column": exc.colno,
            },
        ) from exc

    if not isinstance(parsed, Mapping):
        raise InferenceError(
            ErrorCode.INVALID_MODEL_OUTPUT,
            "Model returned JSON that is not an object.",
            retryable=False,
            details={"format": constraints.format},
        )
    return dict(parsed)
