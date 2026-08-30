"""Canonical refresh-stable routes for the Local LLM Studio browser surface."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

_STUDIO_ROUTES = (
    "/overview",
    "/models",
    "/endpoints",
    "/playground",
    "/evaluations",
    "/system",
    "/settings",
)


def _studio_index() -> FileResponse:
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return FileResponse(static_file)
    raise HTTPException(status_code=404, detail="Web UI file index.html not found.")


def install_studio_ui_routes(application: FastAPI) -> FastAPI:
    """Install the canonical Studio routes exactly once.

    The legacy root route remains a compatibility entry point. Canonical product
    navigation uses the explicit routes below so refresh/back/forward semantics
    do not depend on client-only tab state.
    """
    if getattr(application.state, "studio_ui_routes_installed", False):
        return application
    application.state.studio_ui_routes_installed = True

    for route_path in _STUDIO_ROUTES:
        route_name = f"studio_{route_path.strip('/').replace('-', '_')}"
        application.add_api_route(
            route_path,
            _studio_index,
            methods=["GET"],
            include_in_schema=False,
            name=route_name,
        )

    def model_detail(opaque_model_id: str) -> FileResponse:
        del opaque_model_id
        return _studio_index()

    def evaluation_detail(opaque_run_id: str) -> FileResponse:
        del opaque_run_id
        return _studio_index()

    application.add_api_route(
        "/models/{opaque_model_id}",
        model_detail,
        methods=["GET"],
        include_in_schema=False,
        name="studio_model_detail",
    )
    application.add_api_route(
        "/evaluations/{opaque_run_id}",
        evaluation_detail,
        methods=["GET"],
        include_in_schema=False,
        name="studio_evaluation_detail",
    )
    return application
