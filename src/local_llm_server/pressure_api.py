"""Admin-only dry-run evaluation for host memory pressure and residency policy.

The endpoint samples the host on explicit POST requests and advances the
hysteretic policy state, but it never unloads a runtime. This makes pressure
policy behavior observable on representative devices before any automatic action
is enabled.
"""
from __future__ import annotations

import platform
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from .residency_pressure import PressureEvictionPolicy
from .resources import (
    ResourceObserver,
    ResourceValue,
    StandardLibraryResourceObserver,
    classify_memory_pressure,
)
from .resources_macos import MacOSResourceObserver


def install_pressure_dry_run_api(
    application: FastAPI,
    *,
    observer: ResourceObserver | None = None,
    policy: PressureEvictionPolicy | None = None,
) -> FastAPI:
    """Install one explicit, stateful, non-destructive pressure evaluator."""
    if getattr(application.state, "pressure_dry_run_api_installed", False):
        return application
    application.state.pressure_dry_run_api_installed = True

    settings = getattr(application.state, "settings", None)
    if not bool(getattr(settings, "enable_admin_api", False)):
        return application

    application.state.pressure_dry_run_observer = observer or _default_observer()
    application.state.pressure_eviction_policy = policy or PressureEvictionPolicy()

    def evaluate_pressure(request: Request) -> dict[str, Any]:
        manager = request.app.state.runtime_manager
        residency_snapshot = getattr(manager, "residency_policy_snapshot", None)
        if not callable(residency_snapshot):
            raise HTTPException(
                status_code=501,
                detail="Runtime manager does not expose residency policy state.",
            )

        resource_snapshot = request.app.state.pressure_dry_run_observer.snapshot()
        pressure = classify_memory_pressure(resource_snapshot)
        evaluation = request.app.state.pressure_eviction_policy.observe(
            pressure,
            residency_snapshot(),
        )
        return {
            "mode": "dry_run",
            "action_executed": False,
            "resource": {
                "platform": resource_snapshot.platform,
                "total_memory_bytes": _resource_value(resource_snapshot.total_memory_bytes),
                "available_memory_bytes": _resource_value(resource_snapshot.available_memory_bytes),
                "thermal_pressure": _resource_value(resource_snapshot.thermal_pressure),
            },
            "evaluation": evaluation.to_public_dict(),
            "claim_boundary": (
                "Dry-run pressure policy only. No runtime was unloaded and no "
                "memory-reclamation or production-safety claim is made."
            ),
        }

    application.add_api_route(
        "/api/v1/residency/pressure/evaluate",
        evaluate_pressure,
        methods=["POST"],
        tags=["Resources"],
        name="evaluate_residency_pressure_dry_run",
    )
    return application


def _default_observer() -> ResourceObserver:
    if platform.system().lower() == "darwin":
        return MacOSResourceObserver()
    return StandardLibraryResourceObserver()


def _resource_value(value: ResourceValue) -> dict[str, object]:
    return {
        "value": value.value,
        "source": value.source.value,
        "unit": value.unit,
    }
