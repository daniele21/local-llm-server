"""Supported product HTTP composition outside the legacy server monolith."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from .control_plane_api import install_product_api
from .request_middleware import install_request_policy
from .streaming_metrics import install_streaming_metrics


def install_product_http_stack(
    application: FastAPI,
    *,
    evaluation_root: Path | None = None,
) -> FastAPI:
    """Install canonical policy, live stream timing and modular product APIs.

    Ordering is intentional. ``install_streaming_metrics`` is registered after
    request policy, so its outer middleware can measure the full request while
    reading the canonical request state populated by the inner policy layer once
    ``call_next`` returns a streaming response.
    """
    install_request_policy(application)
    install_streaming_metrics(application)
    install_product_api(application, evaluation_root=evaluation_root)
    return application
