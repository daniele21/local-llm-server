"""Lifecycle, routing, and concurrency ownership for resident model engines."""
from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .resource_manager import AdmissionDecision, AdmissionResult, ResourceManager
from .runtime_admission import admission_metadata, estimated_runtime_load_bytes


def _close_engine(engine: Any) -> None:
    close = getattr(engine, "close", None) or getattr(engine, "shutdown", None)
    if close is not None:
        close()


_BACKEND_CONFIG_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "llama_cpp": (
        "ctx_size", "n_gpu_layers", "n_threads", "n_batch", "n_ubatch",
        "timeout", "offload_kqv", "flash_attn", "use_mmap",
    ),
    "llama_server": (
        "ctx_size",
        "n_threads",
        "n_batch",
        "n_ubatch",
        "timeout",
        "flash_attn",
        "max_concurrent_requests",
        "llama_server_cont_batching",
        "llama_server_kv_unified",
        "llama_server_gpu_layers",
        "llama_server_load_mode",
        "llama_server_fit",
        "llama_server_fit_target_mib",
        "llama_server_fit_ctx",
        "llama_server_cache_type_k",
        "llama_server_cache_type_v",
        "llama_server_cache_ram_mib",
    ),
    "mlx": ("max_kv_size",),
    "mlx_vlm_server": ("timeout", "max_concurrent_requests", "max_kv_size"),
}


def config_capabilities_for_backend(
    backend: str, *, thinking_mode: str = "none"
) -> list[str]:
    """Return settings consumed by both the backend and the selected model."""
    capabilities = list(_BACKEND_CONFIG_CAPABILITIES.get(backend, ()))
    if thinking_mode == "switchable":
        capabilities.extend(("enable_thinking", "show_thinking"))
    elif thinking_mode == "always":
        capabilities.append("show_thinking")
    return capabilities


def new_runtime_status(model_id: str) -> dict[str, Any]:
    return {
        "active": False,
        "active_requests": 0,
        "phase": "idle",
        "tokens_generated": 0,
        "output_chunks": 0,
        "output_characters": 0,
        "max_tokens": 0,
        "started_at": 0.0,
        "last_token_at": 0.0,
        "tokens_per_second": 0.0,
        "model": model_id,
        "last_content": "",
    }


class RuntimeState(str, Enum):
    STARTING = "starting"
    READY = "ready"
    DRAINING = "draining"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class ResourceAdmissionError(RuntimeError):
    """Raised before/after load when configured resource admission rejects it."""

    def __init__(self, result: AdmissionResult) -> None:
        self.result = result
        super().__init__(result.reason)


@dataclass
class ModelRuntime:
    key: str
    cfg: dict[str, Any]
    engine: Any
    admission: threading.Semaphore = field(init=False, repr=False)
    status_lock: threading.Lock = field(default_factory=threading.Lock)
    status: dict[str, Any] = field(default_factory=dict)
    loaded_at: float = field(default_factory=time.time)
    state: RuntimeState = RuntimeState.READY
    active_requests: int = 0
    resource_reservation_id: str | None = None

    def __post_init__(self) -> None:
        concurrency = max(1, int(self.cfg.get("max_concurrent_requests") or 1))
        self.admission = threading.Semaphore(concurrency)
        if not self.status:
            self.status = new_runtime_status(str(self.cfg["model_id"]))

    @property
    def model_id(self) -> str:
        return str(self.cfg["model_id"])

    @property
    def backend(self) -> str:
        return str(self.cfg.get("backend", getattr(self.engine, "backend", "unknown")))

    @property
    def busy(self) -> bool:
        return self.active_requests > 0

    def mark_start(self, max_tokens: int) -> None:
        with self.status_lock:
            self.status.update({
                "active": True,
                "active_requests": self.active_requests,
                "phase": "prefill",
                "tokens_generated": 0,
                "output_chunks": 0,
                "output_characters": 0,
                "max_tokens": max_tokens,
                "started_at": time.time(),
                "last_token_at": 0.0,
                "tokens_per_second": 0.0,
                "model": self.model_id,
                "last_content": "",
            })

    def mark_chunk(self, content: str, total_tokens: int | None = None) -> None:
        now = time.time()
        with self.status_lock:
            self.status["phase"] = "generating"
            self.status["output_chunks"] += 1
            self.status["output_characters"] += len(content)
            if total_tokens is not None:
                self.status["tokens_generated"] = total_tokens
            self.status["last_token_at"] = now
            self.status["last_content"] = content[-200:]
            elapsed = now - self.status["started_at"]
            if elapsed > 0 and self.status["tokens_generated"]:
                self.status["tokens_per_second"] = self.status["tokens_generated"] / elapsed

    def mark_idle(self) -> None:
        with self.status_lock:
            self.status["active"] = self.active_requests > 0
            self.status["active_requests"] = self.active_requests
            if not self.status["active"]:
                self.status["phase"] = "idle"


@dataclass
class _PendingCleanup:
    engine: Any
    resource_reservation_id: str | None
    reason: str


class ModelRuntimeManager:
    """Own all loaded engines and route model keys/IDs to their runtime.

    Logical residency and resource accounting are deliberately fail-conservative:
    an engine is not declared stopped and its reservation is not released until
    backend teardown succeeds. Engines allocated on a failed load/reload are
    retained internally when cleanup itself fails so shutdown can retry them.
    """

    _PORT_FIELDS = {
        "llama_server": "llama_server_port",
        "mlx_vlm_server": "mlx_vlm_server_port",
    }

    def __init__(
        self,
        default_model: str | None = None,
        *,
        resource_manager: ResourceManager | None = None,
    ) -> None:
        self.default_model = default_model
        self._runtimes: dict[str, ModelRuntime] = {}
        self._aliases: dict[str, str] = {}
        self._loading: set[str] = set()
        self._reserved_ports: set[int] = set()
        self._pending_cleanup: list[_PendingCleanup] = []
        self._manager_lock = threading.RLock()
        self._condition = threading.Condition(self._manager_lock)
        self._resource_manager = resource_manager

    @property
    def resource_manager(self) -> ResourceManager | None:
        return self._resource_manager

    @property
    def pending_cleanup_count(self) -> int:
        with self._manager_lock:
            return len(self._pending_cleanup)

    def add(self, cfg: dict[str, Any], engine: Any, *, key: str | None = None) -> ModelRuntime:
        runtime_key = str(key or cfg["model"])
        model_id = str(cfg["model_id"])
        with self._manager_lock:
            if runtime_key in self._runtimes:
                raise ValueError(f"Model '{runtime_key}' is already loaded.")
            for alias in (runtime_key, model_id):
                owner = self._aliases.get(alias)
                if owner is not None and owner != runtime_key:
                    raise ValueError(f"Alias '{alias}' is already used by loaded model '{owner}'.")
            port_field = self._PORT_FIELDS.get(str(cfg.get("backend")))
            if port_field and cfg.get(port_field) is not None:
                port = int(cfg[port_field])
                if port in self._reserved_ports:
                    raise ValueError(f"Backend port {port} is already reserved.")
                self._reserved_ports.add(port)

            runtime = ModelRuntime(runtime_key, cfg, engine)
            self._runtimes[runtime_key] = runtime
            self._aliases[runtime_key] = runtime_key
            self._aliases[model_id] = runtime_key
            if self.default_model is None:
                self.default_model = runtime_key
            return runtime

    def load(self, model: str, **explicit: Any) -> tuple[ModelRuntime, bool]:
        from .config import build_config
        from .engine import load_llm

        with self._manager_lock:
            existing = self._resolve_unlocked(model)
            if existing is not None:
                return existing, False
            if model in self._loading:
                raise RuntimeError(f"Model '{model}' is already loading.")
            self._loading.add(model)

        reservation_id: str | None = None
        engine = None
        try:
            cfg = build_config(model=model, **explicit)
            cfg = self._assign_private_port(cfg)
            reservation_id = self._reserve_runtime_load(model, cfg)
            engine = load_llm(cfg)
            self._commit_runtime_load(reservation_id, cfg)
            runtime = self.add(cfg, engine, key=model)
            runtime.resource_reservation_id = reservation_id
            return runtime, True
        except Exception as exc:
            if engine is not None:
                cleanup_error = self._cleanup_unpublished_engine(
                    engine,
                    reservation_id,
                    reason=f"failed load for {model}",
                )
                if cleanup_error is not None:
                    raise RuntimeError(
                        f"Model '{model}' load failed and backend cleanup also failed; "
                        "resource accounting was retained."
                    ) from cleanup_error
            elif reservation_id is not None:
                self._rollback_runtime_load(reservation_id)
            raise exc
        finally:
            with self._manager_lock:
                self._loading.discard(model)
                self._condition.notify_all()

    def _assign_private_port(self, cfg: dict[str, Any]) -> dict[str, Any]:
        port_field = self._PORT_FIELDS.get(str(cfg.get("backend")))
        if not port_field:
            return cfg
        candidate = int(cfg.get(port_field) or 0)
        if candidate <= 0:
            return cfg
        with self._manager_lock:
            while candidate in self._reserved_ports:
                candidate += 1
        updated = dict(cfg)
        updated[port_field] = candidate
        return updated

    def resolve(self, model: str | None = None) -> ModelRuntime:
        with self._manager_lock:
            target = model or self.default_model
            if target is None:
                raise LookupError("No default model is loaded.")
            runtime = self._resolve_unlocked(target)
            if runtime is None:
                raise LookupError(f"Model '{target}' is not loaded.")
            return runtime

    def _resolve_unlocked(self, model: str) -> ModelRuntime | None:
        key = self._aliases.get(model, model)
        return self._runtimes.get(key)

    def set_default(self, model: str) -> ModelRuntime:
        runtime = self.resolve(model)
        with self._manager_lock:
            if runtime.state is not RuntimeState.READY:
                raise RuntimeError(f"Model '{runtime.key}' is not ready.")
            self.default_model = runtime.key
        return runtime

    def reload(self, model: str, **explicit: Any) -> ModelRuntime:
        """Replace one idle runtime without publishing an unowned replacement."""
        from .config import build_config
        from .engine import load_llm

        current = self.resolve(model)
        with self._manager_lock:
            if self._runtimes.get(current.key) is not current:
                raise LookupError(f"Model '{model}' is no longer loaded.")
            if current.state is not RuntimeState.READY:
                raise RuntimeError(f"Model '{current.key}' is not ready.")
            if current.active_requests:
                raise RuntimeError(f"Model '{current.key}' has an active request.")
            current.state = RuntimeState.DRAINING

        reservation_id: str | None = None
        new_engine = None
        try:
            cfg = build_config(model=current.key, **explicit)
            with self._manager_lock:
                cfg = self._assign_private_port(cfg)
            reservation_id = self._reserve_runtime_load(current.key, cfg)
            new_engine = load_llm(cfg)
            self._commit_runtime_load(reservation_id, cfg)
            replacement = ModelRuntime(
                current.key,
                cfg,
                new_engine,
                resource_reservation_id=reservation_id,
            )
            with self._manager_lock:
                for alias in (current.key, replacement.model_id):
                    owner = self._aliases.get(alias)
                    if owner is not None and owner != current.key:
                        raise ValueError(
                            f"Alias '{alias}' is already used by loaded model '{owner}'."
                        )
                current.state = RuntimeState.STOPPING
        except Exception as exc:
            if new_engine is not None:
                cleanup_error = self._cleanup_unpublished_engine(
                    new_engine,
                    reservation_id,
                    reason=f"failed replacement for {current.key}",
                )
                if cleanup_error is not None:
                    with self._manager_lock:
                        if self._runtimes.get(current.key) is current:
                            current.state = RuntimeState.READY
                    raise RuntimeError(
                        f"Reload for '{current.key}' failed and replacement cleanup also failed; "
                        "replacement accounting was retained."
                    ) from cleanup_error
            elif reservation_id is not None:
                self._rollback_runtime_load(reservation_id)
            with self._manager_lock:
                if self._runtimes.get(current.key) is current:
                    current.state = RuntimeState.READY
            raise exc

        try:
            _close_engine(current.engine)
        except Exception:
            with self._manager_lock:
                current.state = RuntimeState.FAILED
            cleanup_error = self._cleanup_unpublished_engine(
                replacement.engine,
                replacement.resource_reservation_id,
                reason=f"replacement abandoned after teardown failure for {current.key}",
            )
            if cleanup_error is not None:
                raise RuntimeError(
                    f"Reload for '{current.key}' could not stop the current runtime and "
                    "could not clean up its replacement; both remain accounted."
                ) from cleanup_error
            raise

        self._release_runtime_load(current.resource_reservation_id)
        with self._manager_lock:
            if self._runtimes.get(current.key) is not current:
                current.state = RuntimeState.STOPPED
                cleanup_error = self._cleanup_unpublished_engine(
                    replacement.engine,
                    replacement.resource_reservation_id,
                    reason=f"replacement lost ownership race for {current.key}",
                )
                if cleanup_error is not None:
                    raise RuntimeError(
                        f"Runtime '{current.key}' changed during final reload publication and "
                        "replacement cleanup failed."
                    ) from cleanup_error
                raise RuntimeError(f"Model '{current.key}' changed while reloading.")

            self._runtimes[current.key] = replacement
            for alias, key in list(self._aliases.items()):
                if key == current.key:
                    self._aliases.pop(alias, None)
            self._aliases[current.key] = current.key
            self._aliases[replacement.model_id] = current.key
            if self.default_model == current.key:
                self.default_model = replacement.key
        current.state = RuntimeState.STOPPED
        return replacement

    def list(self) -> list[ModelRuntime]:
        with self._manager_lock:
            return list(self._runtimes.values())

    def unload(self, model: str) -> ModelRuntime:
        return self._unload(model, allow_last=False)

    def _unload(self, model: str, *, allow_last: bool) -> ModelRuntime:
        """Stop one idle runtime before removing routing/accounting ownership."""
        runtime = self.resolve(model)
        with self._manager_lock:
            if self._runtimes.get(runtime.key) is not runtime:
                raise LookupError(f"Model '{model}' is no longer loaded.")
            if runtime.state not in {RuntimeState.READY, RuntimeState.FAILED}:
                raise RuntimeError(f"Model '{runtime.key}' is not ready.")
            if not allow_last and len(self._runtimes) == 1:
                raise RuntimeError("Cannot unload the last resident model.")
            if runtime.active_requests:
                raise RuntimeError(f"Model '{runtime.key}' has an active request.")
            runtime.state = RuntimeState.DRAINING
            runtime.state = RuntimeState.STOPPING

        try:
            _close_engine(runtime.engine)
        except Exception:
            with self._manager_lock:
                runtime.state = RuntimeState.FAILED
            raise

        self._release_runtime_load(runtime.resource_reservation_id)
        with self._manager_lock:
            if self._runtimes.get(runtime.key) is runtime:
                self._runtimes.pop(runtime.key, None)
                for alias, key in list(self._aliases.items()):
                    if key == runtime.key:
                        self._aliases.pop(alias, None)
                if self.default_model == runtime.key:
                    self.default_model = self._next_ready_runtime_key_unlocked()
            runtime.state = RuntimeState.STOPPED
        return runtime

    def shutdown(self, *, timeout_seconds: float = 30.0) -> None:
        """Bound drain time, then stop every idle owned engine fail-conservatively.

        Runtimes that fail to drain or fail backend teardown remain tracked and
        accounted with state ``FAILED``. This is intentionally truthful: process
        exit may later reclaim them, but the manager does not fabricate STOPPED.
        """
        timeout = float(timeout_seconds)
        if timeout < 0:
            raise ValueError("timeout_seconds must be >= 0")

        deadline = time.monotonic() + timeout
        with self._condition:
            runtimes = list(self._runtimes.values())
            for runtime in runtimes:
                if runtime.state is RuntimeState.READY:
                    runtime.state = RuntimeState.DRAINING
            self.default_model = None
            while any(runtime.active_requests for runtime in runtimes):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(timeout=remaining)

        failures: list[str] = []
        for runtime in runtimes:
            with self._manager_lock:
                if self._runtimes.get(runtime.key) is not runtime:
                    continue
                if runtime.active_requests:
                    runtime.state = RuntimeState.FAILED
                    failures.append(
                        f"{runtime.key}: {runtime.active_requests} active request(s) did not drain"
                    )
                    continue
                runtime.state = RuntimeState.STOPPING
            try:
                _close_engine(runtime.engine)
            except Exception as exc:
                with self._manager_lock:
                    runtime.state = RuntimeState.FAILED
                failures.append(f"{runtime.key}: backend teardown failed: {exc}")
                continue

            self._release_runtime_load(runtime.resource_reservation_id)
            with self._manager_lock:
                if self._runtimes.get(runtime.key) is runtime:
                    self._runtimes.pop(runtime.key, None)
                    for alias, key in list(self._aliases.items()):
                        if key == runtime.key:
                            self._aliases.pop(alias, None)
                runtime.state = RuntimeState.STOPPED

        failures.extend(self._retry_pending_cleanup())
        if failures:
            raise RuntimeError("Runtime shutdown incomplete: " + "; ".join(failures))

    def _cleanup_unpublished_engine(
        self,
        engine: Any,
        reservation_id: str | None,
        *,
        reason: str,
    ) -> Exception | None:
        """Close an allocated engine before releasing its provisional accounting."""
        try:
            _close_engine(engine)
        except Exception as exc:
            with self._manager_lock:
                self._pending_cleanup.append(
                    _PendingCleanup(engine, reservation_id, reason)
                )
            return exc
        self._rollback_runtime_load(reservation_id)
        return None

    def _retry_pending_cleanup(self) -> list[str]:
        with self._manager_lock:
            pending = list(self._pending_cleanup)
            self._pending_cleanup.clear()

        failures: list[str] = []
        for item in pending:
            try:
                _close_engine(item.engine)
            except Exception as exc:
                failures.append(f"pending cleanup ({item.reason}): {exc}")
                with self._manager_lock:
                    self._pending_cleanup.append(item)
                continue
            self._release_runtime_load(item.resource_reservation_id)
        return failures

    def _next_ready_runtime_key_unlocked(self) -> str | None:
        return next(
            (
                runtime.key
                for runtime in self._runtimes.values()
                if runtime.state is RuntimeState.READY
            ),
            None,
        )

    def _reserve_runtime_load(self, runtime_key: str, cfg: dict[str, Any]) -> str | None:
        estimate = estimated_runtime_load_bytes(cfg)
        manager = self._resource_manager
        if manager is None or estimate is None:
            return None
        result = manager.reserve(
            owner=f"runtime:{runtime_key}",
            requested_bytes=estimate,
            metadata=admission_metadata(cfg),
        )
        cfg["resource_admission"] = result.to_public_dict()
        if result.decision is AdmissionDecision.REJECT or result.reservation is None:
            raise ResourceAdmissionError(result)
        return result.reservation.reservation_id

    def _commit_runtime_load(self, reservation_id: str | None, cfg: dict[str, Any]) -> None:
        manager = self._resource_manager
        if manager is None or reservation_id is None:
            return
        result = manager.commit(
            reservation_id,
            estimate_bytes=estimated_runtime_load_bytes(cfg),
        )
        if result.decision is AdmissionDecision.REJECT:
            # The caller owns the live backend and must close it before the
            # reservation can truthfully be released.
            raise ResourceAdmissionError(result)

    def _rollback_runtime_load(self, reservation_id: str | None) -> None:
        manager = self._resource_manager
        if manager is not None and reservation_id is not None:
            manager.rollback(reservation_id)

    def _release_runtime_load(self, reservation_id: str | None) -> None:
        manager = self._resource_manager
        if manager is not None and reservation_id is not None:
            manager.release(reservation_id)

    @contextmanager
    def lease_runtime(self, runtime: ModelRuntime) -> Iterator[ModelRuntime]:
        with self._manager_lock:
            if (
                self._runtimes.get(runtime.key) is not runtime
                or runtime.state is not RuntimeState.READY
            ):
                raise LookupError(f"Model '{runtime.key}' is no longer available.")
        acquired = runtime.admission.acquire(blocking=False)
        if not acquired:
            raise RuntimeError(f"Model '{runtime.key}' is at its concurrency limit.")
        with self._condition:
            if (
                self._runtimes.get(runtime.key) is not runtime
                or runtime.state is not RuntimeState.READY
            ):
                runtime.admission.release()
                raise LookupError(f"Model '{runtime.key}' is no longer available.")
            runtime.active_requests += 1
            runtime.mark_idle()
        try:
            yield runtime
        finally:
            with self._condition:
                runtime.active_requests = max(0, runtime.active_requests - 1)
                runtime.mark_idle()
                self._condition.notify_all()
            runtime.admission.release()
