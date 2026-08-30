"""Bounded representative-device evidence for the RRG-5 runtime pressure gate.

The campaign exercises the assembled product boundary with two real resident
runtimes while refusing unsafe host-memory conditions. It records observations,
not a universal performance/reclamation verdict, and never enables automatic
pressure eviction.
"""
from __future__ import annotations

import argparse
import json
import platform
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from fastapi.testclient import TestClient

from .product_composition import install_product_http_stack
from .product_runtime_manager import ProductRuntimeManager
from .resource_manager import ReservationState, ResourceManager
from .resource_policy import ResourcePolicySettings
from .resources import ResourceObserver, SystemResourceSnapshot
from .resources_macos import MacOSResourceObserver
from .runtime_admission import estimated_runtime_load_bytes
from .scheduler_policy import RequestSchedulerSettings
from .server import ServerSettings, create_app

_MIB = 1024 ** 2
_GIB = 1024 ** 3


@dataclass(frozen=True, slots=True)
class RuntimePressureEvidenceOptions:
    model_a: str
    model_b: str
    cycles: int = 2
    max_tokens: int = 32
    queue_capacity: int = 4
    global_max_running: int = 1
    global_queue_capacity: int = 4
    headroom_bytes: int = 512 * _MIB
    success_margin_bytes: int = 512 * _MIB
    host_safety_bytes: int = 2 * _GIB
    settle_seconds: float = 2.0
    backend_a: str | None = None
    backend_b: str | None = None

    def __post_init__(self) -> None:
        if not self.model_a.strip() or not self.model_b.strip():
            raise ValueError("model_a and model_b must be non-empty")
        if self.model_a == self.model_b:
            raise ValueError("RRG-5 requires two distinct model keys")
        if self.cycles < 2:
            raise ValueError("cycles must be >= 2")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if self.queue_capacity < 1 or self.global_queue_capacity < 1:
            raise ValueError("queue capacities must be >= 1")
        if self.global_max_running < 1:
            raise ValueError("global_max_running must be >= 1")
        for name in ("headroom_bytes", "success_margin_bytes", "host_safety_bytes"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0")
        if self.settle_seconds < 0:
            raise ValueError("settle_seconds must be >= 0")


def execute_runtime_pressure_evidence(
    options: RuntimePressureEvidenceOptions,
    *,
    observer: ResourceObserver | None = None,
    config_builder: Callable[..., dict[str, Any]] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    """Run the bounded RRG-5 campaign and return privacy-safe observations."""
    if platform.system().lower() != "darwin" and observer is None:
        raise RuntimeError("RRG-5 representative pressure evidence must run on macOS")

    if config_builder is None:
        from .config import build_config

        config_builder = build_config

    cfg_a = config_builder(model=options.model_a, **_runtime_overrides(options.backend_a))
    cfg_b = config_builder(model=options.model_b, **_runtime_overrides(options.backend_b))
    estimates = {
        options.model_a: estimated_runtime_load_bytes(cfg_a),
        options.model_b: estimated_runtime_load_bytes(cfg_b),
    }
    if any(not isinstance(value, int) or value <= 0 for value in estimates.values()):
        raise RuntimeError(
            "RRG-5 requires a positive pre-load resource estimate for both models."
        )
    combined_estimate = sum(int(value) for value in estimates.values())

    resource_observer = observer or MacOSResourceObserver()
    preflight = resource_observer.snapshot()
    available = _measured_positive(preflight.available_memory_bytes.value)
    if available is None:
        raise RuntimeError("Measured available host memory is required for RRG-5.")
    required_available = (
        combined_estimate + options.success_margin_bytes + options.host_safety_bytes
    )
    if available < required_available:
        raise RuntimeError(
            "RRG-5 safety refusal: available host memory is below the combined "
            "resident estimate plus configured success and host-safety margins."
        )

    usable_budget = combined_estimate + options.success_margin_bytes
    resource_settings = ResourcePolicySettings(
        memory_limit_bytes=usable_budget + options.headroom_bytes,
        headroom_bytes=options.headroom_bytes,
    )
    scheduler_settings = RequestSchedulerSettings(
        queue_capacity=options.queue_capacity,
        global_max_running=options.global_max_running,
        global_queue_capacity=options.global_queue_capacity,
    )

    cycles: list[dict[str, object]] = []
    for cycle_index in range(options.cycles):
        before = resource_observer.snapshot()
        cycle = _run_cycle(
            options,
            cycle_index=cycle_index,
            resource_settings=resource_settings,
            scheduler_settings=scheduler_settings,
            observer=resource_observer,
        )
        if options.settle_seconds:
            sleep(options.settle_seconds)
        after = resource_observer.snapshot()
        cycle["host_before"] = _snapshot_summary(before)
        cycle["host_after_stop"] = _snapshot_summary(after)
        cycle["post_stop_available_delta_bytes"] = _available_delta(before, after)
        cycles.append(cycle)

    complete = all(bool(cycle.get("complete")) for cycle in cycles)
    return {
        "schema_version": 1,
        "procedure": "rrg5_runtime_pressure_v1",
        "models": [options.model_a, options.model_b],
        "cycle_count": options.cycles,
        "combined_resident_estimate_bytes": combined_estimate,
        "host_available_preflight_bytes": available,
        "host_safety_bytes": options.host_safety_bytes,
        "success_margin_bytes": options.success_margin_bytes,
        "headroom_bytes": options.headroom_bytes,
        "scheduler": {
            "per_runtime_queue_capacity": options.queue_capacity,
            "global_max_running": options.global_max_running,
            "global_queue_capacity": options.global_queue_capacity,
            "fairness": "runtime_round_robin",
        },
        "cycles": cycles,
        "complete": complete,
        "automatic_eviction_exercised": False,
        "production_safety_claim": False,
        "reclamation_claim": "observational_only",
        "privacy": {
            "prompt_recorded": False,
            "output_recorded": False,
            "model_path_recorded": False,
        },
    }


def _run_cycle(
    options: RuntimePressureEvidenceOptions,
    *,
    cycle_index: int,
    resource_settings: ResourcePolicySettings,
    scheduler_settings: RequestSchedulerSettings,
    observer: ResourceObserver,
) -> dict[str, object]:
    resources = ResourceManager(resource_settings.budget)
    manager = ProductRuntimeManager(
        default_model=options.model_a,
        resource_manager=resources,
    )
    lease_release = threading.Event()
    lease_entered = threading.Event()
    lease_thread: threading.Thread | None = None
    shutdown_initial_error: str | None = None
    try:
        runtime_a, loaded_a = manager.load(
            options.model_a,
            **_runtime_overrides(options.backend_a),
        )
        runtime_b, loaded_b = manager.load(
            options.model_b,
            **_runtime_overrides(options.backend_b),
        )
        if not loaded_a or not loaded_b:
            raise RuntimeError("RRG-5 expected two fresh runtime loads")

        after_load = observer.snapshot()
        application = create_app(manager, settings=ServerSettings(enable_admin_api=True))
        application.state.resource_policy_settings = resource_settings
        install_product_http_stack(application, scheduler_settings=scheduler_settings)

        pressure = _run_concurrent_pressure(
            application,
            models=(runtime_a.key, runtime_b.key),
            max_tokens=options.max_tokens,
        )
        accounting_after_pressure = _resource_summary(resources)

        manager.unload(runtime_b.key)
        accounting_after_unload = _resource_summary(resources)
        reloaded_b, loaded_again = manager.load(
            options.model_b,
            **_runtime_overrides(options.backend_b),
        )
        if not loaded_again:
            raise RuntimeError("RRG-5 reload did not create a fresh runtime")
        reload_status = _single_chat_status(
            application,
            model=reloaded_b.key,
            max_tokens=options.max_tokens,
        )

        def hold_active_lease() -> None:
            current = manager.resolve(runtime_a.key)
            with manager.lease_runtime(current):
                lease_entered.set()
                lease_release.wait(timeout=30.0)

        lease_thread = threading.Thread(
            target=hold_active_lease,
            name=f"rrg5-active-lease-{cycle_index}",
            daemon=True,
        )
        lease_thread.start()
        if not lease_entered.wait(timeout=5.0):
            raise RuntimeError("RRG-5 could not establish the bounded active lease")

        try:
            manager.shutdown(timeout_seconds=0.0)
        except RuntimeError as exc:
            shutdown_initial_error = type(exc).__name__
        else:
            raise RuntimeError("shutdown unexpectedly completed while an active lease was held")

        retained = _resource_summary(resources)
        active_runtime = manager.resolve(runtime_a.key)
        failed_while_active = active_runtime.state.value == "failed"
        retained_while_active = retained["committed_bytes"] > 0

        lease_release.set()
        lease_thread.join(timeout=5.0)
        if lease_thread.is_alive():
            raise RuntimeError("bounded active lease did not drain")
        manager.shutdown(timeout_seconds=30.0)
        final_accounting = _resource_summary(resources)
        after_shutdown = observer.snapshot()

        complete = bool(
            pressure["all_http_200"]
            and pressure["global_headers_present"]
            and pressure["observed_global_inflight_peak"] <= options.global_max_running
            and reload_status == 200
            and failed_while_active
            and retained_while_active
            and final_accounting["committed_bytes"] == 0
            and final_accounting["reserved_bytes"] == 0
            and final_accounting["reservation_count"] == 0
        )
        return {
            "cycle_index": cycle_index,
            "loaded_models": [runtime_a.key, runtime_b.key],
            "after_load": _snapshot_summary(after_load),
            "pressure": pressure,
            "accounting_after_pressure": accounting_after_pressure,
            "accounting_after_unload": accounting_after_unload,
            "reload_http_status": reload_status,
            "shutdown_under_active_lease": {
                "initial_shutdown_error_type": shutdown_initial_error,
                "runtime_failed_while_active": failed_while_active,
                "accounting_retained_while_active": retained_while_active,
                "retry_shutdown_completed": True,
            },
            "final_accounting": final_accounting,
            "after_shutdown": _snapshot_summary(after_shutdown),
            "complete": complete,
        }
    finally:
        lease_release.set()
        if lease_thread is not None and lease_thread.is_alive():
            lease_thread.join(timeout=1.0)
        if manager.list():
            try:
                manager.shutdown(timeout_seconds=5.0)
            except RuntimeError:
                pass


def _run_concurrent_pressure(
    application: Any,
    *,
    models: tuple[str, str],
    max_tokens: int,
) -> dict[str, object]:
    start = threading.Event()
    results: list[dict[str, object]] = []
    result_lock = threading.Lock()

    def request(model: str) -> None:
        start.wait(timeout=5.0)
        with TestClient(application) as client:
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Return a concise numbered list with four local-AI safety checks.",
                        }
                    ],
                    "temperature": 0.0,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
        with result_lock:
            results.append(
                {
                    "model": model,
                    "http_status": response.status_code,
                    "global_wait_ms": _float_header(
                        response.headers.get("x-local-llm-global-wait-ms")
                    ),
                }
            )

    threads = [
        threading.Thread(target=request, args=(models[0],), daemon=True),
        threading.Thread(target=request, args=(models[1],), daemon=True),
        threading.Thread(target=request, args=(models[0],), daemon=True),
    ]
    for thread in threads:
        thread.start()
    start.set()

    governor = getattr(application.state, "global_execution_governor", None)
    peak_inflight = 0
    peak_queued = 0
    deadline = time.monotonic() + 120.0
    while any(thread.is_alive() for thread in threads):
        if governor is not None:
            snapshot = governor.snapshot()
            peak_inflight = max(peak_inflight, snapshot.inflight)
            peak_queued = max(peak_queued, snapshot.queued)
        if time.monotonic() >= deadline:
            raise RuntimeError("RRG-5 concurrent pressure requests exceeded 120 seconds")
        time.sleep(0.002)
    for thread in threads:
        thread.join(timeout=0.1)

    waits = [item.get("global_wait_ms") for item in results]
    global_headers_present = len(results) == len(threads) and all(
        isinstance(value, float) for value in waits
    )
    return {
        "request_count": len(results),
        "models_completed": sorted(
            {str(item["model"]) for item in results if item.get("http_status") == 200}
        ),
        "all_http_200": len(results) == len(threads)
        and all(item.get("http_status") == 200 for item in results),
        "global_headers_present": global_headers_present,
        "positive_global_wait_observed": any(
            isinstance(value, float) and value > 0 for value in waits
        ),
        "observed_global_inflight_peak": peak_inflight,
        "observed_global_queue_peak": peak_queued,
    }


def _single_chat_status(application: Any, *, model: str, max_tokens: int) -> int:
    with TestClient(application) as client:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "temperature": 0.0,
                "max_tokens": max_tokens,
                "stream": False,
            },
        )
    return response.status_code


def _runtime_overrides(backend: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"no_download": True}
    if backend is not None:
        result["backend"] = backend
    return result


def _measured_positive(value: object) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
        return int(value)
    return None


def _snapshot_summary(snapshot: SystemResourceSnapshot) -> dict[str, object]:
    return {
        "available_memory_bytes": snapshot.available_memory_bytes.value,
        "available_memory_source": snapshot.available_memory_bytes.source.value,
        "process_rss_bytes": snapshot.process_rss_bytes.value,
        "process_rss_source": snapshot.process_rss_bytes.source.value,
    }


def _available_delta(
    before: SystemResourceSnapshot,
    after: SystemResourceSnapshot,
) -> int | None:
    start = _measured_positive(before.available_memory_bytes.value)
    end = _measured_positive(after.available_memory_bytes.value)
    if start is None or end is None:
        return None
    return end - start


def _resource_summary(resources: ResourceManager) -> dict[str, int]:
    reservations = resources.snapshot()
    committed = sum(
        item.accounted_bytes
        for item in reservations
        if item.state is ReservationState.COMMITTED
    )
    reserved = sum(
        item.accounted_bytes
        for item in reservations
        if item.state is ReservationState.RESERVED
    )
    return {
        "committed_bytes": committed,
        "reserved_bytes": reserved,
        "reservation_count": len(reservations),
    }


def _float_header(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def write_runtime_pressure_report(path: str | Path, report: Mapping[str, object]) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp.replace(target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bounded representative-device RRG-5 multi-model pressure evidence."
    )
    parser.add_argument("--model-a", required=True)
    parser.add_argument("--model-b", required=True)
    parser.add_argument("--backend-a", default=None)
    parser.add_argument("--backend-b", default=None)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument("--queue-capacity", type=int, default=4)
    parser.add_argument("--global-max-running", type=int, default=1)
    parser.add_argument("--global-queue-capacity", type=int, default=4)
    parser.add_argument("--headroom-gib", type=float, default=0.5)
    parser.add_argument("--success-margin-gib", type=float, default=0.5)
    parser.add_argument("--host-safety-gib", type=float, default=2.0)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    options = RuntimePressureEvidenceOptions(
        model_a=args.model_a,
        model_b=args.model_b,
        cycles=args.cycles,
        max_tokens=args.max_tokens,
        queue_capacity=args.queue_capacity,
        global_max_running=args.global_max_running,
        global_queue_capacity=args.global_queue_capacity,
        headroom_bytes=int(args.headroom_gib * _GIB),
        success_margin_bytes=int(args.success_margin_gib * _GIB),
        host_safety_bytes=int(args.host_safety_gib * _GIB),
        settle_seconds=args.settle_seconds,
        backend_a=args.backend_a,
        backend_b=args.backend_b,
    )
    report = execute_runtime_pressure_evidence(options)
    output = write_runtime_pressure_report(args.output, report)
    print(f"Runtime-pressure evidence report written to {output.resolve()}")
    if report.get("complete") is not True:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
