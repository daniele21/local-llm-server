"""Administrative residency-policy API for explicit runtime pinning."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field


class RuntimePinBody(BaseModel):
    model: str = Field(..., min_length=1)
    pinned: bool = True


def install_residency_api(application: FastAPI) -> FastAPI:
    """Install privacy-safe residency policy routes when admin API is enabled."""
    if getattr(application.state, "residency_api_installed", False):
        return application
    application.state.residency_api_installed = True

    settings = getattr(application.state, "settings", None)
    if not bool(getattr(settings, "enable_admin_api", False)):
        return application

    def snapshot(request: Request) -> dict[str, Any]:
        manager = request.app.state.runtime_manager
        producer = getattr(manager, "residency_policy_snapshot", None)
        if producer is None:
            raise HTTPException(
                status_code=501,
                detail="Runtime manager does not expose residency policy state.",
            )
        payload = producer()
        return {"supported": True, **payload}

    def set_pin(body: RuntimePinBody, request: Request) -> dict[str, Any]:
        manager = request.app.state.runtime_manager
        setter = getattr(manager, "set_pinned", None)
        producer = getattr(manager, "residency_policy_snapshot", None)
        if setter is None or producer is None:
            raise HTTPException(
                status_code=501,
                detail="Runtime manager does not support residency pinning.",
            )
        try:
            runtime = setter(body.model, body.pinned)
        except LookupError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {
            "ok": True,
            "model": runtime.model_id,
            "key": runtime.key,
            "pinned": body.pinned,
            "residency": producer(),
        }

    application.add_api_route(
        "/api/v1/residency",
        snapshot,
        methods=["GET"],
        tags=["Resources"],
        name="get_residency_policy",
    )
    application.add_api_route(
        "/api/v1/residency/pin",
        set_pin,
        methods=["POST"],
        tags=["Resources"],
        name="set_runtime_pin",
    )
    return application
