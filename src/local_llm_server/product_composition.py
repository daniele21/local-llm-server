"""Supported product HTTP composition outside the legacy server monolith."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .completion_metrics import install_completion_metrics
from .control_plane_api import install_product_api
from .policy_evidence import install_policy_evidence_api
from .pressure_api import install_pressure_dry_run_api
from .request_middleware import install_request_policy
from .request_scheduler import install_request_scheduler
from .residency_api import install_residency_api
from .scheduler_policy import RequestSchedulerSettings
from .streaming_metrics import install_streaming_metrics


def install_product_http_stack(
    application: FastAPI,
    *,
    evaluation_root: Path | None = None,
    scheduler_settings: RequestSchedulerSettings | None = None,
) -> FastAPI:
    """Install admission, policy, truthful timing and modular product APIs.

    Starlette executes the last-added HTTP middleware outermost. Registration is
    intentionally scheduler -> canonical policy -> completion metrics -> stream
    metrics. At execution time stream timing is outermost, completion metrics
    handles only non-stream requests, policy prepares the canonical request and
    scheduler gates it before the route/runtime lease. Product API installs the
    cold-state layer last. Residency/policy/pressure routes remain admin-only;
    pressure evaluation is explicit dry-run state and never unloads a runtime.
    """
    install_request_scheduler(application, settings=scheduler_settings)
    install_request_policy(application)
    install_completion_metrics(application)
    install_streaming_metrics(application)
    install_product_api(application, evaluation_root=evaluation_root)
    install_residency_api(application)
    install_policy_evidence_api(application)
    install_pressure_dry_run_api(application)
    return application
