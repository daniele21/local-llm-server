"""Supported product HTTP composition outside the legacy server monolith."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .control_plane_api import install_product_api
from .request_middleware import install_request_policy
from .request_scheduler import install_request_scheduler
from .scheduler_policy import RequestSchedulerSettings
from .streaming_metrics import install_streaming_metrics


def install_product_http_stack(
    application: FastAPI,
    *,
    evaluation_root: Path | None = None,
    scheduler_settings: RequestSchedulerSettings | None = None,
) -> FastAPI:
    """Install request admission, policy, live timing and modular product APIs.

    Starlette executes the last-added HTTP middleware outermost. Registration is
    therefore intentionally scheduler -> canonical policy -> streaming timing:
    streaming timing observes the whole request, canonical policy prepares the
    backend-neutral request, and the scheduler consumes that prepared request
    before the route acquires the runtime lease. Product API installs cold-state
    handling last as the outer product-state layer.
    """
    install_request_scheduler(application, settings=scheduler_settings)
    install_request_policy(application)
    install_streaming_metrics(application)
    install_product_api(application, evaluation_root=evaluation_root)
    return application
