"""Bounded representative-Mac probe for the RRG-5 double-load boundary.

This diagnostic intentionally stops before inference. It reproduces the same
verified-artifact, resource-budget and runtime-manager path used by RRG-5, then
classifies a load failure without serializing backend logs, model paths, PIDs,
prompts or outputs.
"""
from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from typing import Any, Mapping

from .artifact_verification import verified_receipt_for_config
from .config import build_config
from .multi_model_device_evidence import (
    MultiModelDeviceEvidenceOptions,
    _EvidenceResourceManager,
    _build_model_spec,
    _numeric_value,
    _snapshot_to_public_dict,
)
from .product_runtime_manager import ProductRuntimeManager
from .resources import ResourceBudget
from .resources_macos import MacOSResourceObserver
from .runtime import ResourceAdmissionError

_MIB = 1024**2
_GIB = 1024**3
_EXIT_CODE = re.compile(r"exited during startup with code\s+(-?\d+)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RRG5PairLoadProbeOptions:
    model_a: str
    model_b: str
    request_estimate_bytes: int
    model_a_path: str | None = None
    model_b_path: str | None = None
    backend: str = "llama_server"
    headroom_bytes: int = 512 * _MIB
    success_margin_bytes: int = 512 * _MIB
    host_safety_bytes: int = 2 * _GIB


def classify_pair_load_failure(exc: BaseException) -> dict[str, object]:
    """Return a bounded category from a potentially private backend exception."""
    text = str(exc).lower()
    category = "backend_startup_failure"
    if isinstance(exc, ResourceAdmissionError):
        category = "resource_admission"
    elif isinstance(exc, TimeoutError) or "did not become ready" in text:
        category = "startup_timeout"
    elif any(token in text for token in (
        "address already in use",
        "failed to bind",
        "bind() failed",
        "bind failed",
        "cannot bind",
    )):
        category = "port_bind"
    elif any(token in text for token in (
        "out of memory",
        "cannot allocate memory",
        "failed to allocate",
        "allocation failed",
        "metal buffer allocation",
        "failed allocating",
    )):
        category = "memory_allocation"
    elif any(token in text for token in (
        "unknown argument",
        "unrecognized option",
        "unrecognized argument",
        "invalid option",
        "unknown option",
    )):
        category = "runtime_cli_incompatibility"
    elif any(token in text for token in (
        "failed to load model",
        "error loading model",
        "llama_model_load",
        "failed to open gguf",
        "invalid model",
        "unsupported model",
        "model load failed",
    )):
        category = "model_load"
    elif "exited during startup" in text:
        category = "backend_startup_exit"

    match = _EXIT_CODE.search(str(exc))
    return {
        "category": category,
        "error_type": type(exc).__name__,
        "startup_exit_code": int(match.group(1)) if match else None,
        "raw_error_retained": False,
    }


def run_rrg5_pair_load_probe(options: RRG5PairLoadProbeOptions) -> dict[str, object]:
    """Exercise only the two-resident load boundary and clean up owned runtimes."""
    if platform.system().lower() != "darwin":
        raise RuntimeError("RRG-5 pair-load probe must run on macOS")
    if options.model_a == options.model_b:
        raise ValueError("pair-load probe requires two distinct model keys")
    if options.request_estimate_bytes <= 0:
        raise ValueError("request_estimate_bytes must be positive")

    shared = MultiModelDeviceEvidenceOptions(
        model_a=options.model_a,
        model_b=options.model_b,
        request_estimate_bytes=options.request_estimate_bytes,
        model_a_path=options.model_a_path,
        model_b_path=options.model_b_path,
        backend=options.backend,
        headroom_bytes=options.headroom_bytes,
        success_margin_bytes=options.success_margin_bytes,
        host_safety_bytes=options.host_safety_bytes,
    )
    resolve_receipt = lambda cfg: verified_receipt_for_config(cfg)
    spec_a = _build_model_spec(
        options.model_a,
        options.model_a_path,
        shared,
        config_builder=build_config,
        receipt_resolver=resolve_receipt,
    )
    spec_b = _build_model_spec(
        options.model_b,
        options.model_b_path,
        shared,
        config_builder=build_config,
        receipt_resolver=resolve_receipt,
    )

    observer = MacOSResourceObserver()
    before = observer.snapshot()
    available = _numeric_value(before.available_memory_bytes)
    resident_bytes = spec_a.estimate_bytes + spec_b.estimate_bytes
    transient_capacity_bytes = 2 * options.request_estimate_bytes
    usable_budget = resident_bytes + transient_capacity_bytes + options.success_margin_bytes
    required_available = usable_budget + options.host_safety_bytes
    budget = ResourceBudget(
        limit_bytes=usable_budget + options.headroom_bytes,
        headroom_bytes=options.headroom_bytes,
    )
    result: dict[str, object] = {
        "schema_version": 1,
        "procedure": "rrg5_pair_load_probe_v1",
        "models": [spec_a.to_public_dict(), spec_b.to_public_dict()],
        "budget": {
            "resident_estimate_bytes": resident_bytes,
            "transient_capacity_bytes": transient_capacity_bytes,
            "usable_budget_bytes": budget.usable_bytes,
            "required_available_before_bytes": required_available,
        },
        "host_before": _snapshot_to_public_dict(before),
        "status": "incomplete",
        "failed_phase": None,
        "failure": None,
        "model_a_loaded": False,
        "model_b_loaded": False,
        "private_ports": {},
        "raw_backend_logs_retained": False,
    }
    if available is None or available <= 0 or available < required_available:
        result["status"] = "refused_host_safety"
        return result

    resources = _EvidenceResourceManager(budget)
    manager = ProductRuntimeManager(default_model=spec_a.key, resource_manager=resources)
    phase = "load_model_a"
    try:
        runtime_a, loaded_a = manager.load(spec_a.key, **dict(spec_a.overrides))
        if not loaded_a:
            raise RuntimeError("model_a was unexpectedly already resident")
        result["model_a_loaded"] = True
        result["private_ports"] = {
            "model_a": runtime_a.cfg.get("llama_server_port"),
        }
        result["host_after_model_a"] = _snapshot_to_public_dict(observer.snapshot())

        phase = "load_model_b"
        runtime_b, loaded_b = manager.load(spec_b.key, **dict(spec_b.overrides))
        if not loaded_b:
            raise RuntimeError("model_b was unexpectedly already resident")
        result["model_b_loaded"] = True
        result["private_ports"] = {
            "model_a": runtime_a.cfg.get("llama_server_port"),
            "model_b": runtime_b.cfg.get("llama_server_port"),
        }
        result["host_after_model_b"] = _snapshot_to_public_dict(observer.snapshot())
        result["status"] = "complete"
    except Exception as exc:  # noqa: BLE001 - classify without retaining raw error
        result["failed_phase"] = phase
        result["failure"] = classify_pair_load_failure(exc)
    finally:
        result["configured_accounting_peak"] = resources.peak_snapshot()
        try:
            manager.shutdown(timeout_seconds=30.0)
            result["cleanup_complete"] = True
        except RuntimeError:
            result["cleanup_complete"] = False
        result["configured_accounting_after_cleanup"] = resources.current_snapshot()
    return result
