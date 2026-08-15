"""Privacy-safe product policy evidence for Settings/control-plane consumers."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request


def policy_evidence_payload(application: Any) -> dict[str, object]:
    """Expose effective policy flags without paths, prompts or secret values."""
    manager = getattr(application.state, "runtime_manager", None)
    runtimes = manager.list() if manager is not None else []
    return {
        "canonical_request_policy_installed": bool(
            getattr(application.state, "canonical_request_policy_installed", False)
        ),
        "remote_media_default": "blocked",
        "trust_remote_code_default": False,
        "runtimes": [
            {
                "key": runtime.key,
                "model": runtime.model_id,
                "allow_remote_media": bool(runtime.cfg.get("allow_remote_media", False)),
                "trust_remote_code": bool(runtime.cfg.get("trust_remote_code", False)),
            }
            for runtime in runtimes
        ],
    }


def install_policy_evidence_api(application: FastAPI) -> FastAPI:
    """Install the read-only policy evidence route when admin API is enabled."""
    if getattr(application.state, "policy_evidence_api_installed", False):
        return application
    application.state.policy_evidence_api_installed = True

    settings = getattr(application.state, "settings", None)
    if not bool(getattr(settings, "enable_admin_api", False)):
        return application

    def get_policy_evidence(request: Request) -> dict[str, object]:
        return policy_evidence_payload(request.app)

    application.add_api_route(
        "/api/v1/policies",
        get_policy_evidence,
        methods=["GET"],
        tags=["Resources"],
        name="get_product_policy_evidence",
    )
    return application
