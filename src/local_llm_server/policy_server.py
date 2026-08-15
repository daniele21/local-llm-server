"""Policy-enabled HTTP server entrypoint.

This wrapper composes the existing FastAPI application/runtime manager with the
canonical request-policy middleware without editing the historical server
monolith. It is the public/CLI server path while the legacy module-level app is
kept for backward compatibility.
"""
from __future__ import annotations

from typing import Any


def run_server(
    cfg: dict[str, Any],
    llm: Any,
    manager: Any | None = None,
    *,
    enable_admin_api: bool = False,
    cors_origins: list[str] | tuple[str, ...] | None = None,
) -> None:
    import uvicorn

    from .request_middleware import install_request_policy
    from .server import (
        ServerSettings,
        begin_app_shutdown,
        configure_runtime,
        create_app,
    )

    application = create_app(
        settings=ServerSettings(
            enable_admin_api=enable_admin_api,
            cors_origins=tuple(cors_origins or ()),
        )
    )
    manager = configure_runtime(cfg, llm, manager, target_app=application)
    install_request_policy(application)
    resolved_cfg = manager.resolve().cfg

    config = uvicorn.Config(
        application,
        host=resolved_cfg["host"],
        port=resolved_cfg["port"],
        log_level="warning" if not resolved_cfg.get("verbose", False) else "info",
        timeout_graceful_shutdown=10,
    )
    server = uvicorn.Server(config)

    try:
        server.run()
    finally:
        begin_app_shutdown(application)
        manager.shutdown()
