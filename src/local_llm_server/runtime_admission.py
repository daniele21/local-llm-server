"""Helpers used when applying ResourceManager admission to real runtime loads."""
from __future__ import annotations

from typing import Any, Mapping

from .memory_envelope import MemoryEnvelope, resident_memory_envelope
from .resource_manager import AdmissionResult


def estimated_runtime_load_bytes(config: Mapping[str, Any]) -> int | None:
    """Return the attributable configured resident estimate used for admission.

    The value may be a partial lower-bound estimate when some envelope
    components are unavailable. ``resident_memory_envelope`` retains that
    completeness information; this compatibility helper keeps the existing
    runtime admission API stable while adding configured component costs.
    """
    return resident_memory_envelope(config).accounted_bytes


def runtime_envelope_metadata(config: Mapping[str, Any]) -> dict[str, object]:
    """Return path-free resident envelope evidence for control-plane surfaces."""
    return _envelope_metadata(resident_memory_envelope(config))


def admission_metadata(
    result: AdmissionResult | None,
    *,
    estimate_bytes: int | None,
) -> dict[str, object]:
    if result is None:
        return {
            "decision": "unknown",
            "estimate_bytes": estimate_bytes,
            "reason": "resource manager not configured or no enforceable estimate",
        }
    return {
        "decision": result.decision.value,
        "estimate_bytes": estimate_bytes,
        "usable_budget_bytes": result.usable_budget_bytes,
        "reason": result.reason,
    }


def _envelope_metadata(envelope: MemoryEnvelope) -> dict[str, object]:
    return envelope.as_dict()
