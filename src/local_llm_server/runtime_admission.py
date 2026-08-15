"""Helpers used when applying ResourceManager admission to real runtime loads."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .resource_manager import AdmissionResult

_GIB = 1024 ** 3


def estimated_runtime_load_bytes(config: Mapping[str, Any]) -> int | None:
    """Return a pre-load estimate without pretending it is measured residency.

    Registry ``size_gb`` is explicitly treated as an estimate. For direct local
    files the artifact file size is a fallback estimate. Directory traversal is
    deliberately avoided here; MLX snapshot sizing should be supplied by
    registry/resource metadata rather than adding an unbounded pre-load scan.
    """
    explicit = config.get("resource_estimate_bytes")
    if isinstance(explicit, int) and not isinstance(explicit, bool) and explicit >= 0:
        return explicit

    size_gb = config.get("size_gb")
    if isinstance(size_gb, (int, float)) and not isinstance(size_gb, bool) and size_gb >= 0:
        return int(float(size_gb) * _GIB)

    model_path = config.get("model_path")
    if isinstance(model_path, str) and model_path:
        path = Path(model_path).expanduser()
        try:
            if path.is_file():
                return path.stat().st_size
        except OSError:
            return None
    return None


def admission_metadata(result: AdmissionResult | None, *, estimate_bytes: int | None) -> dict[str, object]:
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
