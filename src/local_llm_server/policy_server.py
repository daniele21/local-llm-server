"""Policy-enabled HTTP server entrypoint.

This wrapper composes the existing FastAPI application/runtime manager with the
canonical request-policy middleware and modular product APIs without editing the
historical server monolith.
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
    resource_policy_settings: Any | None = None,
) -> None:
    import uvicorn

    from .control_plane_api import install_product_api
    from .product_runtime import effective_policy_for_manager
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
    application.state.resource_policy_settings = (
        resource_policy_settings
        if resource_policy_settings is not None
        else effective_policy_for_manager(manager)
    )
    install_request_policy(application)
    install_product_api(application)
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
