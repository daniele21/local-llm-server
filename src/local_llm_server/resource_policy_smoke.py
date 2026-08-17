"""Bounded real-device resource-policy smoke procedure.

This module is intentionally separate from CI evidence. On macOS it checks a
measured host-memory safety margin before loading a real model, exercises the
product API through load/inference/unload accounting, then proves a deliberately
insufficient configured budget rejects without creating residency. It never
induces critical pressure or allocates memory merely to trigger rejection.
"""
from __future__ import annotations

import argparse
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from .product_composition import install_product_http_stack
from .product_runtime_manager import ProductRuntimeManager
from .resource_manager import ResourceManager
from .resource_policy import ResourcePolicySettings
from .resources_macos import MacOSResourceObserver
from .runtime import ResourceAdmissionError
from .runtime_admission import estimated_runtime_load_bytes
from .server import ServerSettings, create_app

_MIB = 1024 ** 2
_GIB = 1024 ** 3


@dataclass(frozen=True, slots=True)
class ResourcePolicySmokeOptions:
    model: str
    model_path: str | None = None
    backend: str | None = None
    prompt: str = "Reply with the single word OK."
    max_tokens: int = 8
    headroom_bytes: int = 512 * _MIB
    success_margin_bytes: int = 512 * _MIB
    host_safety_bytes: int = 2 * _GIB

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")
        for name in ("headroom_bytes", "success_margin_bytes", "host_safety_bytes"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")


def execute_resource_policy_smoke(
    options: ResourcePolicySmokeOptions,
    *,
    observer: MacOSResourceObserver | None = None,
) -> dict[str, object]:
    """Execute the bounded product smoke and return path/prompt-free evidence."""
    if platform.system().lower() != "darwin" and observer is None:
        raise RuntimeError("RES-2 real-device smoke must run on macOS")

    from .config import build_config

    explicit = _runtime_overrides(options)
    cfg = build_config(model=options.model, **explicit)
    estimate = estimated_runtime_load_bytes(cfg)
    if estimate is None or estimate <= 0:
        raise RuntimeError(
            "Cannot run bounded resource smoke without a positive pre-load resource estimate."
        )

    host_snapshot = (observer or MacOSResourceObserver()).snapshot()
    available = host_snapshot.available_memory_bytes.value
    if not isinstance(available, (int, float)) or available <= 0:
        raise RuntimeError("Measured available host memory is required for the bounded smoke.")

    required_available = estimate + options.success_margin_bytes + options.host_safety_bytes
    if available < required_available:
        raise RuntimeError(
            "Bounded smoke refused: measured available host memory is below the "
            "artifact estimate plus configured success and host-safety margins."
        )

    success_usable = estimate + options.success_margin_bytes
    success_settings = ResourcePolicySettings(
        memory_limit_bytes=success_usable + options.headroom_bytes,
        headroom_bytes=options.headroom_bytes,
    )
    success = _run_success_case(options, explicit, success_settings)

    reject_usable = max(0, estimate - 1)
    reject_settings = ResourcePolicySettings(
        memory_limit_bytes=reject_usable + options.headroom_bytes,
        headroom_bytes=options.headroom_bytes,
    )
    rejected = _run_reject_case(options, explicit, reject_settings)

    return {
        "schema_version": 1,
        "procedure": "bounded_resource_policy_smoke",
        "model": options.model,
        "backend": cfg.get("backend"),
        "estimate_bytes": estimate,
        "host_available_before_bytes": int(available),
        "host_safety_bytes": options.host_safety_bytes,
        "success_margin_bytes": options.success_margin_bytes,
        "headroom_bytes": options.headroom_bytes,
        "success": success,
        "rejection": rejected,
        "automatic_eviction_exercised": False,
    }


def _run_success_case(
    options: ResourcePolicySmokeOptions,
    explicit: dict[str, Any],
    settings: ResourcePolicySettings,
) -> dict[str, object]:
    resources = ResourceManager(settings.budget)
    manager = ProductRuntimeManager(
        default_model=options.model,
        resource_manager=resources,
    )
    try:
        runtime, loaded = manager.load(options.model, **explicit)
        if not loaded:
            raise RuntimeError("Expected a fresh runtime load for the success smoke.")

        application = create_app(
            manager,
            settings=ServerSettings(enable_admin_api=True),
        )
        application.state.resource_policy_settings = settings
        install_product_http_stack(application)
        with TestClient(application) as client:
            committed = client.get("/api/v1/resources")
            committed.raise_for_status()
            committed_payload = committed.json()
            if committed_payload.get("committed_bytes", 0) <= 0:
                raise RuntimeError("Runtime load did not become committed in resource accounting.")

            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": runtime.key,
                    "messages": [{"role": "user", "content": options.prompt}],
                    "temperature": 0.0,
                    "max_tokens": options.max_tokens,
                },
            )
            response.raise_for_status()

            unload = client.delete(f"/api/v1/models/{runtime.key}")
            unload.raise_for_status()
            released = client.get("/api/v1/resources")
            released.raise_for_status()
            released_payload = released.json()
            health = client.get("/health")
            health.raise_for_status()
            health_payload = health.json()

        if released_payload.get("committed_bytes") != 0:
            raise RuntimeError("Committed accounting did not return to zero after unload.")
        if released_payload.get("reserved_bytes") != 0:
            raise RuntimeError("Reserved accounting did not return to zero after unload.")
        if released_payload.get("reservation_count") != 0:
            raise RuntimeError("Resource reservations remain after unload.")
        if health_payload.get("ok") is not True or health_payload.get("state") != "cold":
            raise RuntimeError("Product health is not green/cold after final unload.")

        return {
            "admission": "admit",
            "loaded": True,
            "inference_http_status": response.status_code,
            "committed_bytes": committed_payload.get("committed_bytes"),
            "reserved_bytes_after_unload": released_payload.get("reserved_bytes"),
            "committed_bytes_after_unload": released_payload.get("committed_bytes"),
            "reservation_count_after_unload": released_payload.get("reservation_count"),
            "health_ok_after_unload": health_payload.get("ok"),
            "health_state_after_unload": health_payload.get("state"),
        }
    finally:
        manager.shutdown()


def _run_reject_case(
    options: ResourcePolicySmokeOptions,
    explicit: dict[str, Any],
    settings: ResourcePolicySettings,
) -> dict[str, object]:
    resources = ResourceManager(settings.budget)
    manager = ProductRuntimeManager(
        default_model=options.model,
        resource_manager=resources,
    )
    try:
        try:
            manager.load(options.model, **explicit)
        except ResourceAdmissionError as exc:
            result = exc.result
        else:
            raise RuntimeError("Insufficient-budget smoke unexpectedly loaded the backend.")

        if manager.list():
            raise RuntimeError("Rejected model became resident unexpectedly.")
        if resources.snapshot():
            raise RuntimeError("Rejected load left resource reservations behind.")

        return {
            "admission": result.decision.value,
            "reason": result.reason,
            "resident_count_after_reject": 0,
            "reservation_count_after_reject": 0,
            "backend_load_reached": False,
        }
    finally:
        manager.shutdown()


def _runtime_overrides(options: ResourcePolicySmokeOptions) -> dict[str, Any]:
    explicit: dict[str, Any] = {"no_download": True}
    if options.model_path is not None:
        explicit["model_path"] = options.model_path
    if options.backend is not None:
        explicit["backend"] = options.backend
    return explicit


def write_smoke_report(path: str | Path, report: dict[str, object]) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded real-device resource-policy smoke.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--backend", default=None)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--headroom-gib", type=float, default=0.5)
    parser.add_argument("--success-margin-gib", type=float, default=0.5)
    parser.add_argument("--host-safety-gib", type=float, default=2.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    options = ResourcePolicySmokeOptions(
        model=args.model,
        model_path=args.model_path,
        backend=args.backend,
        max_tokens=args.max_tokens,
        headroom_bytes=int(args.headroom_gib * _GIB),
        success_margin_bytes=int(args.success_margin_gib * _GIB),
        host_safety_bytes=int(args.host_safety_gib * _GIB),
    )
    report = execute_resource_policy_smoke(options)
    output = write_smoke_report(args.output, report)
    print(f"Resource-policy smoke report written to {output.resolve()}")


if __name__ == "__main__":
    main()
