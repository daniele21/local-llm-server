"""Healthy zero-resident product-state middleware."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def install_cold_state(application: FastAPI) -> FastAPI:
    """Keep supported product apps healthy when no runtime is resident."""
    if getattr(application.state, "cold_state_installed", False):
        return application
    application.state.cold_state_installed = True

    @application.middleware("http")
    async def cold_state_middleware(request: Request, call_next):
        manager = getattr(request.app.state, "runtime_manager", None)
        if manager is None:
            return await call_next(request)
        runtimes = manager.list()
        if runtimes:
            return await call_next(request)

        # Clear stale compatibility references after the last runtime unloads.
        request.app.state.llm = None
        request.app.state.cfg = None

        if request.method.upper() == "GET" and request.url.path == "/health":
            settings = getattr(request.app.state, "settings", None)
            endpoints = [
                "GET /health",
                "GET /v1/models",
                "POST /v1/chat/completions",
                "POST /v1/audio/transcriptions",
                "GET /status",
            ]
            if bool(getattr(settings, "enable_admin_api", False)):
                endpoints.extend(
                    [
                        "GET /api/v1/models/registry",
                        "GET /api/v1/resources",
                        "GET /api/v1/evidence",
                        "GET /api/v1/evaluation/test-sets",
                        "POST /api/v1/evaluation/runs",
                    ]
                )
            return JSONResponse(
                {
                    "ok": True,
                    "server": "local-llm-server",
                    "state": "cold",
                    "resident": False,
                    "backend": None,
                    "model": None,
                    "default_model": None,
                    "configured_default_model": getattr(
                        manager, "configured_default_model", None
                    ),
                    "loaded_models": [],
                    "admin_api_enabled": bool(
                        getattr(settings, "enable_admin_api", False)
                    ),
                    "endpoints": endpoints,
                }
            )

        return await call_next(request)

    return application
