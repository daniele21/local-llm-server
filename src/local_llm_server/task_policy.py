"""Canonical request capability enforcement before backend invocation."""
from __future__ import annotations

from typing import Any, Mapping

from .core import ErrorCode, InferenceError, InferenceRequest
from .core.capabilities import CapabilityDescriptor, descriptor_from_registry_entry


def capability_descriptor_for_runtime(
    runtime_config: Mapping[str, Any],
) -> CapabilityDescriptor:
    """Build the proven capability descriptor from the effective runtime config."""
    try:
        return descriptor_from_registry_entry(runtime_config)
    except ValueError as exc:
        raise InferenceError(
            ErrorCode.INVALID_REQUEST,
            "The selected runtime has an invalid capability declaration.",
            retryable=False,
            details={"policy": "invalid_runtime_capabilities"},
        ) from exc


def enforce_request_capabilities(
    request: InferenceRequest,
    *,
    runtime_config: Mapping[str, Any],
) -> CapabilityDescriptor:
    descriptor = capability_descriptor_for_runtime(runtime_config)
    if descriptor.supports(request):
        return descriptor

    details = {
        "task": request.task.value,
        "stream": request.stream,
        "capabilities": descriptor.to_dict(),
    }
    raise InferenceError(
        ErrorCode.UNSUPPORTED_TASK,
        "The selected runtime does not support the requested task or feature set.",
        retryable=False,
        details=details,
    )
