"""Representative-device evidence for the multi-model resource governor.

This procedure is deliberately separate from deterministic CI and the existing
single-worker reclamation campaign. It exercises two real resident runtimes,
cross-runtime HTTP concurrency, shared transient accounting, lease-safe shutdown
under load and post-stop macOS observations without enabling automatic eviction.

The serialized report omits prompts, model paths, process IDs and model outputs.
Configured accounting and OS measurements are reported as different evidence
classes; neither is silently promoted into a reclamation verdict.
"""
from __future__ import annotations

import argparse
import json
import platform
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from fastapi.testclient import TestClient

from .artifact_verification import ArtifactVerificationStore, verified_receipt_for_config
from .config import build_config
from .product_composition import install_product_http_stack
from .product_runtime_manager import ProductRuntimeManager
from .resource_manager import ReservationKind, ReservationState, ResourceManager
from .resource_policy import ResourcePolicySettings
from .resources import (
    ResourceBudget,
    ResourceObserver,
    ResourceValue,
    ResourceValueSource,
    SystemResourceSnapshot,
    classify_memory_pressure,
)
from .resources_macos import MacOSResourceObserver, read_process_rss
from .residency_pressure import PressureEvictionPolicy
from .runtime import ModelRuntime
from .runtime_admission import estimated_runtime_load_bytes
from .runtime_evidence import attached_runtime_identity
from .scheduler_policy import RequestSchedulerSettings
from .server import ServerSettings, create_app

_MIB = 1024**2
_GIB = 1024**3


@dataclass(frozen=True, slots=True)
class MultiModelDeviceEvidenceOptions:
    model_a: str
    model_b: str
    request_estimate_bytes: int
    model_a_path: str | None = None
    model_b_path: str | None = None
    backend: str | None = None
    cycles: int = 2
    max_tokens: int = 8
    prompt: str = "Reply with the single word OK."
    headroom_bytes: int = 512 * _MIB
    success_margin_bytes: int = 512 * _MIB
    host_safety_bytes: int = 2 * _GIB
    settle_seconds: float = 2.0
    shutdown_timeout_seconds: float = 0.05
    sample_interval_seconds: float = 0.05
    global_max_running: int = 2
    global_queue_capacity: int = 4

    def __post_init__(self) -> None:
        if not self.model_a.strip() or not self.model_b.strip():
            raise ValueError("model_a and model_b must be non-empty")
        if self.model_a == self.model_b:
            raise ValueError("multi-model evidence requires two distinct model keys")
        if self.cycles < 1:
            raise ValueError("cycles must be >= 1")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if self.request_estimate_bytes < 1:
            raise ValueError("request_estimate_bytes must be >= 1")
        if self.settle_seconds < 0:
            raise ValueError("settle_seconds must be >= 0")
        if self.shutdown_timeout_seconds < 0:
            raise ValueError("shutdown_timeout_seconds must be >= 0")
        if self.sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds must be > 0")
        if self.global_max_running < 2:
            raise ValueError("global_max_running must be >= 2 for cross-runtime evidence")
        if self.global_queue_capacity < 1:
            raise ValueError("global_queue_capacity must be >= 1")
        for name in ("headroom_bytes", "success_margin_bytes", "host_safety_bytes"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")


@dataclass(frozen=True, slots=True)
class _ModelSpec:
    key: str
    model_id: str
    backend: str
    estimate_bytes: int
    artifact_sha256: str
    overrides: Mapping[str, Any]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "model_id": self.model_id,
            "backend": self.backend,
            "estimate_bytes": self.estimate_bytes,
            "artifact_sha256": self.artifact_sha256,
        }


class _EvidenceResourceManager(ResourceManager):
    """Record aggregate configured-accounting peaks without changing admission."""

    def __init__(self, budget: ResourceBudget) -> None:
        super().__init__(budget)
        self._evidence_lock = threading.RLock()
        self._peaks = {
            "resident_committed_bytes": 0,
            "resident_reserved_bytes": 0,
            "transient_committed_bytes": 0,
            "transient_reserved_bytes": 0,
            "reservation_count": 0,
        }

    def reserve(self, *args, **kwargs):
        result = super().reserve(*args, **kwargs)
        self._record_peak()
        return result

    def commit(self, *args, **kwargs):
        result = super().commit(*args, **kwargs)
        self._record_peak()
        return result

    def release(self, *args, **kwargs):
        result = super().release(*args, **kwargs)
        self._record_peak()
        return result

    def peak_snapshot(self) -> dict[str, int]:
        with self._evidence_lock:
            return dict(self._peaks)

    def current_snapshot(self) -> dict[str, int]:
        return _aggregate_accounting(self)

    def _record_peak(self) -> None:
        current = _aggregate_accounting(self)
        with self._evidence_lock:
            for key, value in current.items():
                self._peaks[key] = max(self._peaks[key], value)


def execute_multi_model_device_evidence(
    options: MultiModelDeviceEvidenceOptions,
    *,
    observer: ResourceObserver | None = None,
    verification_store: ArtifactVerificationStore | None = None,
    config_builder: Callable[..., dict[str, Any]] = build_config,
    receipt_resolver: Callable[[Mapping[str, Any]], Any | None] | None = None,
    backend_rss_reader: Callable[[int], ResourceValue] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Run bounded multi-model evidence and return a privacy-safe report."""
    if platform.system().lower() != "darwin" and observer is None:
        raise RuntimeError("RRG-5 multi-model evidence must run on macOS")

    resource_observer = observer or MacOSResourceObserver()
    resolve_receipt = receipt_resolver or (
        lambda cfg: verified_receipt_for_config(cfg, store=verification_store)
    )
    rss_reader = backend_rss_reader or read_process_rss
    spec_a = _build_model_spec(
        options.model_a,
        options.model_a_path,
        options,
        config_builder=config_builder,
        receipt_resolver=resolve_receipt,
    )
    spec_b = _build_model_spec(
        options.model_b,
        options.model_b_path,
        options,
        config_builder=config_builder,
        receipt_resolver=resolve_receipt,
    )
    if spec_a.model_id == spec_b.model_id:
        raise RuntimeError("RRG-5 requires two runtime identities that can be resident together")

    before = resource_observer.snapshot()
    available = _numeric_value(before.available_memory_bytes)
    if available is None or available <= 0:
        raise RuntimeError("Measured available host memory is required for RRG-5 evidence")

    resident_bytes = spec_a.estimate_bytes + spec_b.estimate_bytes
    transient_capacity_bytes = options.global_max_running * options.request_estimate_bytes
    usable_budget = resident_bytes + transient_capacity_bytes + options.success_margin_bytes
    required_available = usable_budget + options.host_safety_bytes
    budget = ResourceBudget(
        limit_bytes=usable_budget + options.headroom_bytes,
        headroom_bytes=options.headroom_bytes,
    )

    base_report: dict[str, object] = {
        "schema_version": 1,
        "procedure": {
            "name": "multi_model_resource_governor_v1",
            "cycles": options.cycles,
            "max_tokens": options.max_tokens,
            "request_estimate_bytes": options.request_estimate_bytes,
            "global_max_running": options.global_max_running,
            "global_queue_capacity": options.global_queue_capacity,
            "settle_after_unload_seconds": options.settle_seconds,
            "shutdown_timeout_seconds": options.shutdown_timeout_seconds,
            "sample_interval_seconds": options.sample_interval_seconds,
            "prompt_recorded": False,
            "output_recorded": False,
            "process_ids_recorded": False,
            "automatic_eviction_enabled": False,
        },
        "models": [spec_a.to_public_dict(), spec_b.to_public_dict()],
        "budget": {
            "resident_estimate_bytes": resident_bytes,
            "transient_capacity_bytes": transient_capacity_bytes,
            "success_margin_bytes": options.success_margin_bytes,
            "headroom_bytes": options.headroom_bytes,
            "host_safety_bytes": options.host_safety_bytes,
            "usable_budget_bytes": budget.usable_bytes,
            "required_available_before_bytes": required_available,
        },
        "host_before": _snapshot_to_public_dict(before),
        "cycles": [],
        "shutdown_under_load": None,
        "complete": False,
        "automatic_eviction_exercised": False,
    }

    if available < required_available:
        base_report["status"] = "refused_host_safety"
        base_report["refusal"] = {
            "available_before_bytes": int(available),
            "required_available_before_bytes": required_available,
        }
        return base_report

    cycles: list[dict[str, object]] = []
    for cycle_index in range(options.cycles):
        cycle = _run_multi_model_cycle(
            cycle_index + 1,
            options,
            (spec_a, spec_b),
            budget,
            resource_observer,
            rss_reader,
            sleep,
        )
        cycles.append(cycle)
        if not bool(cycle.get("complete")):
            break
    base_report["cycles"] = cycles

    shutdown = _run_shutdown_under_load(
        options,
        (spec_a, spec_b),
        budget,
        resource_observer,
        rss_reader,
        sleep,
    )
    base_report["shutdown_under_load"] = shutdown

    all_cycles_complete = len(cycles) == options.cycles and all(
        bool(cycle.get("complete")) for cycle in cycles
    )
    base_report["complete"] = all_cycles_complete and bool(shutdown.get("complete"))
    base_report["status"] = "complete" if base_report["complete"] else "incomplete"
    return base_report


def _build_model_spec(
    model: str,
    model_path: str | None,
    options: MultiModelDeviceEvidenceOptions,
    *,
    config_builder: Callable[..., dict[str, Any]],
    receipt_resolver: Callable[[Mapping[str, Any]], Any | None],
) -> _ModelSpec:
    overrides: dict[str, Any] = {
        "no_download": True,
        "resource_request_estimate_bytes": options.request_estimate_bytes,
        "max_concurrent_requests": 1,
    }
    if options.backend is not None:
        overrides["backend"] = options.backend
    preview = config_builder(model=model, model_path=model_path, **overrides)
    estimate = estimated_runtime_load_bytes(preview)
    if estimate is None or estimate <= 0:
        raise RuntimeError(
            f"Model '{model}' has no positive resident estimate for bounded RRG-5 evidence"
        )
    receipt = receipt_resolver(preview)
    if receipt is None:
        raise RuntimeError(
            f"Model '{model}' requires a current verified artifact receipt before RRG-5 evidence"
        )
    sha256 = str(getattr(receipt, "sha256", "")).lower()
    if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
        raise RuntimeError(f"Model '{model}' artifact receipt has no valid SHA-256 identity")
    overrides["artifact_sha256"] = sha256
    return _ModelSpec(
        key=model,
        model_id=str(preview.get("model_id") or model),
        backend=str(preview.get("backend") or "unknown"),
        estimate_bytes=int(estimate),
        artifact_sha256=sha256,
        overrides=overrides,
    )


def _run_multi_model_cycle(
    cycle_number: int,
    options: MultiModelDeviceEvidenceOptions,
    specs: tuple[_ModelSpec, _ModelSpec],
    budget: ResourceBudget,
    observer: ResourceObserver,
    backend_rss_reader: Callable[[int], ResourceValue],
    sleep: Callable[[float], None],
) -> dict[str, object]:
    resources = _EvidenceResourceManager(budget)
    manager = ProductRuntimeManager(default_model=specs[0].key, resource_manager=resources)
    phase = "start"
    before_load = observer.snapshot()
    host_snapshots: dict[str, dict[str, object]] = {
        "before_load": _snapshot_to_public_dict(before_load)
    }
    identities: list[dict[str, object] | None] = []
    pressure_evaluation: dict[str, object] | None = None
    responses: list[dict[str, object]] = []
    try:
        phase = "load_model_a"
        runtime_a, loaded_a = manager.load(specs[0].key, **dict(specs[0].overrides))
        if not loaded_a:
            raise RuntimeError("model_a was unexpectedly already resident")
        after_a = observer.snapshot()
        host_snapshots["after_model_a"] = _snapshot_to_public_dict(
            after_a,
            owned_backend_rss=_owned_backend_rss(manager, backend_rss_reader),
        )

        phase = "load_model_b"
        runtime_b, loaded_b = manager.load(specs[1].key, **dict(specs[1].overrides))
        if not loaded_b:
            raise RuntimeError("model_b was unexpectedly already resident")
        after_b = observer.snapshot()
        after_b_backend_rss = _owned_backend_rss(manager, backend_rss_reader)
        host_snapshots["after_model_b"] = _snapshot_to_public_dict(
            after_b,
            owned_backend_rss=after_b_backend_rss,
        )
        identities = [_runtime_identity_dict(runtime_a), _runtime_identity_dict(runtime_b)]

        settings = ResourcePolicySettings(
            memory_limit_bytes=int(budget.limit_bytes or 0),
            headroom_bytes=budget.headroom_bytes,
        )
        application = create_app(
            manager,
            settings=ServerSettings(enable_admin_api=True),
        )
        application.state.resource_policy_settings = settings
        install_product_http_stack(
            application,
            scheduler_settings=RequestSchedulerSettings(
                global_max_running=options.global_max_running,
                global_queue_capacity=options.global_queue_capacity,
            ),
        )

        phase = "concurrent_inference"
        peak_pressure_snapshot = after_b
        peak_backend_rss = after_b_backend_rss
        with TestClient(application) as client:
            start_barrier = threading.Barrier(2)

            def invoke(runtime: ModelRuntime) -> dict[str, object]:
                start_barrier.wait(timeout=10)
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": runtime.key,
                        "messages": [{"role": "user", "content": options.prompt}],
                        "temperature": 0.0,
                        "max_tokens": options.max_tokens,
                    },
                )
                return {
                    "model": runtime.key,
                    "http_status": response.status_code,
                    "global_wait_ms": _optional_float(
                        response.headers.get("x-local-llm-global-wait-ms")
                    ),
                }

            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="rrg5") as executor:
                futures = [executor.submit(invoke, runtime) for runtime in (runtime_a, runtime_b)]
                while not all(future.done() for future in futures):
                    sampled = observer.snapshot()
                    sampled_backend_rss = _owned_backend_rss(manager, backend_rss_reader)
                    if _available_fraction(sampled) < _available_fraction(peak_pressure_snapshot):
                        peak_pressure_snapshot = sampled
                        peak_backend_rss = sampled_backend_rss
                    sleep(options.sample_interval_seconds)
                responses = [future.result() for future in futures]

            after_requests = observer.snapshot()
            after_requests_backend_rss = _owned_backend_rss(manager, backend_rss_reader)
            if _available_fraction(after_requests) < _available_fraction(peak_pressure_snapshot):
                peak_pressure_snapshot = after_requests
                peak_backend_rss = after_requests_backend_rss
            host_snapshots["during_concurrent_pressure_peak"] = _snapshot_to_public_dict(
                peak_pressure_snapshot,
                owned_backend_rss=peak_backend_rss,
            )
            host_snapshots["after_concurrent_inference"] = _snapshot_to_public_dict(
                after_requests,
                owned_backend_rss=after_requests_backend_rss,
            )
            pressure_evaluation = PressureEvictionPolicy().observe(
                classify_memory_pressure(peak_pressure_snapshot),
                manager.residency_policy_snapshot(),
            ).to_public_dict()

            phase = "unload"
            for runtime in (runtime_a, runtime_b):
                response = client.delete(f"/api/v1/models/{runtime.key}")
                if response.status_code >= 400:
                    raise RuntimeError("runtime unload failed during RRG-5 cycle")

        if options.settle_seconds > 0:
            sleep(options.settle_seconds)
        after_unload = observer.snapshot()
        host_snapshots["after_unload_settle"] = _snapshot_to_public_dict(
            after_unload,
            owned_backend_rss=_owned_backend_rss(manager, backend_rss_reader),
        )
        final_accounting = resources.current_snapshot()
        peaks = resources.peak_snapshot()
        statuses_ok = all(item["http_status"] == 200 for item in responses)
        transient_overlap = (
            peaks["transient_committed_bytes"] >= 2 * options.request_estimate_bytes
        )
        clean = final_accounting["reservation_count"] == 0 and not manager.list()
        return {
            "cycle": cycle_number,
            "complete": statuses_ok and transient_overlap and clean,
            "responses": responses,
            "configured_accounting_peak": peaks,
            "configured_accounting_after_unload": final_accounting,
            "concurrent_transient_overlap_observed": transient_overlap,
            "host": host_snapshots,
            "post_stop_observation": _post_stop_observation(host_snapshots),
            "pressure_policy_dry_run": pressure_evaluation,
            "runtime_identities": identities,
            "automatic_eviction_exercised": False,
        }
    except Exception as exc:
        return {
            "cycle": cycle_number,
            "complete": False,
            "failed_phase": phase,
            "error_type": type(exc).__name__,
            "responses": responses,
            "configured_accounting_peak": resources.peak_snapshot(),
            "configured_accounting_current": resources.current_snapshot(),
            "host": host_snapshots,
            "pressure_policy_dry_run": pressure_evaluation,
            "runtime_identities": identities,
            "automatic_eviction_exercised": False,
        }
    finally:
        try:
            manager.shutdown(timeout_seconds=30.0)
        except RuntimeError:
            pass


def _run_shutdown_under_load(
    options: MultiModelDeviceEvidenceOptions,
    specs: tuple[_ModelSpec, _ModelSpec],
    budget: ResourceBudget,
    observer: ResourceObserver,
    backend_rss_reader: Callable[[int], ResourceValue],
    sleep: Callable[[float], None],
) -> dict[str, object]:
    resources = _EvidenceResourceManager(budget)
    manager = ProductRuntimeManager(default_model=specs[0].key, resource_manager=resources)
    lease_ready = threading.Event()
    release_lease = threading.Event()
    holder_error: list[str] = []
    holder: threading.Thread | None = None
    phase = "load"
    before = _snapshot_to_public_dict(observer.snapshot())
    try:
        runtime_a, _ = manager.load(specs[0].key, **dict(specs[0].overrides))
        manager.load(specs[1].key, **dict(specs[1].overrides))
        loaded_host = _snapshot_to_public_dict(
            observer.snapshot(),
            owned_backend_rss=_owned_backend_rss(manager, backend_rss_reader),
        )

        def hold_lease() -> None:
            try:
                with manager.lease_runtime(runtime_a):
                    lease_ready.set()
                    release_lease.wait(timeout=30.0)
            except Exception as exc:  # pragma: no cover - retained as evidence
                holder_error.append(type(exc).__name__)
                lease_ready.set()

        holder = threading.Thread(target=hold_lease, name="rrg5-held-runtime-lease")
        holder.start()
        if not lease_ready.wait(timeout=10.0):
            raise RuntimeError("held runtime lease did not become active")
        if holder_error:
            raise RuntimeError("held runtime lease failed before shutdown evidence")

        phase = "bounded_shutdown"
        first_shutdown_failed = False
        try:
            manager.shutdown(timeout_seconds=options.shutdown_timeout_seconds)
        except RuntimeError:
            first_shutdown_failed = True

        after_first = _snapshot_to_public_dict(
            observer.snapshot(),
            owned_backend_rss=_owned_backend_rss(manager, backend_rss_reader),
        )
        remaining = [
            {
                "key": runtime.key,
                "state": runtime.state.value,
                "active_requests": runtime.active_requests,
            }
            for runtime in manager.list()
        ]
        accounting_after_first = resources.current_snapshot()
        lease_owner_retained = any(
            item["key"] == runtime_a.key
            and item["state"] == "failed"
            and int(item["active_requests"]) > 0
            for item in remaining
        )

        phase = "release_and_retry"
        release_lease.set()
        holder.join(timeout=10.0)
        if holder.is_alive():
            raise RuntimeError("held runtime lease did not release")
        manager.shutdown(timeout_seconds=30.0)
        if options.settle_seconds > 0:
            sleep(options.settle_seconds)
        after_retry = _snapshot_to_public_dict(
            observer.snapshot(),
            owned_backend_rss=_owned_backend_rss(manager, backend_rss_reader),
        )
        final_accounting = resources.current_snapshot()
        retry_clean = not manager.list() and final_accounting["reservation_count"] == 0
        return {
            "complete": (
                first_shutdown_failed
                and lease_owner_retained
                and not holder_error
                and retry_clean
            ),
            "first_shutdown_reported_incomplete": first_shutdown_failed,
            "active_owner_retained_after_timeout": lease_owner_retained,
            "remaining_after_first_shutdown": remaining,
            "configured_accounting_after_first_shutdown": accounting_after_first,
            "configured_accounting_after_retry": final_accounting,
            "configured_accounting_peak": resources.peak_snapshot(),
            "host_before": before,
            "host_after_load": loaded_host,
            "host_after_first_shutdown": after_first,
            "host_after_retry_settle": after_retry,
            "post_stop_observation": _post_stop_observation(
                {
                    "before_load": before,
                    "after_model_b": loaded_host,
                    "after_unload_settle": after_retry,
                }
            ),
            "automatic_eviction_exercised": False,
        }
    except Exception as exc:
        return {
            "complete": False,
            "failed_phase": phase,
            "error_type": type(exc).__name__,
            "configured_accounting_current": resources.current_snapshot(),
            "host_before": before,
            "automatic_eviction_exercised": False,
        }
    finally:
        release_lease.set()
        if holder is not None:
            holder.join(timeout=10.0)
        try:
            manager.shutdown(timeout_seconds=30.0)
        except RuntimeError:
            pass


def _aggregate_accounting(manager: ResourceManager) -> dict[str, int]:
    values = {
        "resident_committed_bytes": 0,
        "resident_reserved_bytes": 0,
        "transient_committed_bytes": 0,
        "transient_reserved_bytes": 0,
        "reservation_count": 0,
    }
    reservations = manager.snapshot()
    values["reservation_count"] = len(reservations)
    for reservation in reservations:
        prefix = "resident" if reservation.kind is ReservationKind.RESIDENT else "transient"
        suffix = (
            "committed_bytes"
            if reservation.state is ReservationState.COMMITTED
            else "reserved_bytes"
        )
        values[f"{prefix}_{suffix}"] += reservation.accounted_bytes
    return values


def _owned_backend_rss(
    manager: ProductRuntimeManager,
    reader: Callable[[int], ResourceValue],
) -> dict[str, object]:
    pids: list[int] = []
    for runtime in manager.list():
        managed = getattr(runtime.engine, "process", None)
        process = getattr(managed, "process", None)
        pid = getattr(process, "pid", None)
        if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
            pids.append(pid)
    if not pids:
        return {
            "value": None,
            "source": "not_applicable",
            "unit": "bytes",
            "owner_count": 0,
        }
    measurements = [reader(pid) for pid in pids]
    if any(item.source is ResourceValueSource.UNAVAILABLE for item in measurements):
        return {
            "value": None,
            "source": "unavailable",
            "unit": "bytes",
            "owner_count": len(pids),
        }
    return {
        "value": sum(int(item.value or 0) for item in measurements),
        "source": "measured",
        "unit": "bytes",
        "owner_count": len(pids),
    }


def _snapshot_to_public_dict(
    snapshot: SystemResourceSnapshot,
    *,
    owned_backend_rss: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "platform": snapshot.platform,
        "total_memory_bytes": _value_to_public_dict(snapshot.total_memory_bytes),
        "available_memory_bytes": _value_to_public_dict(snapshot.available_memory_bytes),
        "process_rss_bytes": _value_to_public_dict(snapshot.process_rss_bytes),
        "owned_backend_rss_bytes": dict(owned_backend_rss) if owned_backend_rss else None,
        "accelerator_memory_bytes": _value_to_public_dict(snapshot.accelerator_memory_bytes),
        "pressure": classify_memory_pressure(snapshot).value,
    }


def _value_to_public_dict(value: ResourceValue) -> dict[str, object]:
    return {"value": value.value, "source": value.source.value, "unit": value.unit}


def _numeric_value(value: ResourceValue) -> int | float | None:
    if isinstance(value.value, (int, float)) and not isinstance(value.value, bool):
        return value.value
    return None


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _runtime_identity_dict(runtime: ModelRuntime) -> dict[str, object] | None:
    identity = attached_runtime_identity(runtime)
    return identity.to_public_dict() if identity is not None else None


def _available_fraction(snapshot: SystemResourceSnapshot) -> float:
    total = _numeric_value(snapshot.total_memory_bytes)
    available = _numeric_value(snapshot.available_memory_bytes)
    if total is None or available is None or total <= 0:
        return float("inf")
    return float(available) / float(total)


def _post_stop_observation(
    snapshots: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    before = snapshots.get("before_load")
    loaded = snapshots.get("after_model_b")
    after = snapshots.get("after_unload_settle")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return {
            "rss_after_minus_before_bytes": None,
            "available_after_minus_before_bytes": None,
            "interpretation": "observational_only",
        }
    result: dict[str, object] = {
        "rss_after_minus_before_bytes": _serialized_delta(
            before.get("process_rss_bytes"), after.get("process_rss_bytes")
        ),
        "available_after_minus_before_bytes": _serialized_delta(
            before.get("available_memory_bytes"), after.get("available_memory_bytes")
        ),
        "interpretation": "observational_only",
    }
    if isinstance(loaded, Mapping):
        loaded_backend = loaded.get("owned_backend_rss_bytes")
        after_backend = after.get("owned_backend_rss_bytes")
        if isinstance(loaded_backend, Mapping):
            result["owned_backend_rss_before_stop_bytes"] = loaded_backend.get("value")
            result["owned_backend_owner_count_before_stop"] = loaded_backend.get("owner_count")
        if isinstance(after_backend, Mapping):
            result["owned_backend_rss_after_stop_bytes"] = after_backend.get("value")
            result["owned_backend_owner_count_after_stop"] = after_backend.get("owner_count")
    return result


def _serialized_delta(before: object, after: object) -> int | float | None:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return None
    left = before.get("value")
    right = after.get("value")
    if (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
    ):
        return right - left
    return None


def write_multi_model_evidence_report(
    path: str | Path,
    report: Mapping[str, object],
) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bounded RRG-5 multi-model evidence on a representative Mac."
    )
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--model-a-path", default=None)
    parser.add_argument("--model-b-path", default=None)
    parser.add_argument(
        "--backend",
        choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"],
        default=None,
    )
    parser.add_argument("--request-estimate-mib", type=float, required=True)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--prompt", default="Reply with the single word OK.")
    parser.add_argument("--headroom-gib", type=float, default=0.5)
    parser.add_argument("--success-margin-gib", type=float, default=0.5)
    parser.add_argument("--host-safety-gib", type=float, default=2.0)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument("--shutdown-timeout-ms", type=float, default=50.0)
    parser.add_argument("--sample-interval-ms", type=float, default=50.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    options = MultiModelDeviceEvidenceOptions(
        model_a=args.model_a,
        model_b=args.model_b,
        request_estimate_bytes=int(args.request_estimate_mib * _MIB),
        model_a_path=args.model_a_path,
        model_b_path=args.model_b_path,
        backend=args.backend,
        cycles=args.cycles,
        max_tokens=args.max_tokens,
        prompt=args.prompt,
        headroom_bytes=int(args.headroom_gib * _GIB),
        success_margin_bytes=int(args.success_margin_gib * _GIB),
        host_safety_bytes=int(args.host_safety_gib * _GIB),
        settle_seconds=args.settle_seconds,
        shutdown_timeout_seconds=args.shutdown_timeout_ms / 1000.0,
        sample_interval_seconds=args.sample_interval_ms / 1000.0,
    )
    report = execute_multi_model_device_evidence(options)
    output = write_multi_model_evidence_report(args.output, report)
    print(f"RRG-5 multi-model evidence report written to {output.resolve()}")
    if not report.get("complete"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
