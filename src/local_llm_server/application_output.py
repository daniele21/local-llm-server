"""Canonical application-output normalization shared by interactive and evaluation paths.

Reasoning separation always precedes structured-output validation. This module
never extracts a JSON-looking substring and never repairs malformed JSON.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core.capabilities import ThinkingMode, effective_thinking_mode
from .core.contracts import OutputConstraints
from .reasoning_boundary import split_reasoning_content
from .structured_output import parse_structured_output


@dataclass(frozen=True, slots=True)
class NormalizedApplicationOutput:
    raw_content: str
    reasoning: str
    final_content: str
    structured_output: Mapping[str, Any] | None


def normalize_application_output(
    content: str,
    *,
    expect_reasoning: bool,
    constraints: OutputConstraints,
) -> NormalizedApplicationOutput:
    """Separate reasoning, then strictly validate the complete final answer."""
    reasoning, final_content = split_reasoning_content(
        content,
        expect_reasoning=expect_reasoning,
    )
    structured = parse_structured_output(final_content, constraints)
    return NormalizedApplicationOutput(
        raw_content=content,
        reasoning=reasoning,
        final_content=final_content,
        structured_output=structured,
    )


def request_expects_reasoning(
    enable_thinking: bool | None,
    runtime_config: Mapping[str, Any],
) -> bool:
    """Resolve the effective execution state used by final-answer normalization."""
    mode = effective_thinking_mode(runtime_config)
    if mode is ThinkingMode.NONE:
        return False
    if mode is ThinkingMode.ALWAYS:
        return True
    if enable_thinking is not None:
        return bool(enable_thinking)

    configured = runtime_config.get("enable_thinking")
    if configured is None:
        params = runtime_config.get("params")
        if isinstance(params, Mapping):
            configured = params.get("enable_thinking")
    return bool(configured)
