"""Lifecycle, routing, and concurrency ownership for resident model engines."""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from collections.abc import Iterator
from typing import Any


def _close_engine(engine: Any) -> None:
    close = getattr(engine, "close", None) or getattr(engine, "shutdown", None)
    if close is not None:
        close()


_BACKEND_CONFIG_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "llama_cpp": (
        "ctx_size", "n_gpu_layers", "n_threads", "n_batch", "n_ubatch",
        "timeout", "offload_kqv", "flash_attn", "use_mmap",
    ),
    "llama_server": ("ctx_size", "timeout", "max_concurrent_requests"),
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
    READY = "ready"
    DRAINING = "draining"
    STOPPED = "stopped"
    FAILED = "failed"


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

    def __post_init__(self) -> None:
        concurrency = max(1, int(self.cfg.get("max_concurrent_requests") or 1))
        self.admission = threading.Semaphore(concurrency)
        if not self.status:
            self.status = new_runtime_status(str(self.cfg["model_id"]))

    @property
    def model_id(self) -> str:
        return str(self.cfg["model_id"])

    def snapshot_status(self) -> dict[str, Any]:
        with self.status_lock:
            result = dict(self.status)
        if result["active"] and result["phase"] == "generating" and result["output_chunks"] > 0:
            elapsed = time.perf_counter() - result["started_at"]
            if elapsed > 0:
                result["chunks_per_second"] = result["output_chunks"] / elapsed
        result["key"] = self.key
        result["backend"] = getattr(self.engine, "backend", self.cfg.get("backend", "unknown"))
        result["loaded_at"] = self.loaded_at
        result["state"] = self.state.value
        result["active_requests"] = self.active_requests
        result["max_concurrent_requests"] = int(
            self.cfg.get("max_concurrent_requests") or 1
        )
        return result

    def mark_started(self, max_tokens: int) -> None:
        with self.status_lock:
            if not self.status["active"]:
                self.status.update({
                    "phase": "prompt_eval",
                    "tokens_generated": 0,
                    "output_chunks": 0,
                    "output_characters": 0,
                    "max_tokens": max_tokens,
                    "started_at": time.perf_counter(),
                    "last_content": "",
                })
            self.status["active"] = True
            self.status["active_requests"] = self.active_requests

    def mark_generating(self) -> None:
        with self.status_lock:
            self.status["phase"] = "generating"
            self.status["started_at"] = time.perf_counter()

    def record_output(self, content: str, *, full_content: str | None = None) -> None:
        with self.status_lock:
            self.status["output_chunks"] += 1
            self.status["output_characters"] += len(content)
            # Deprecated compatibility field; use output_chunks for new clients.
            self.status["tokens_generated"] = self.status["output_chunks"]
            self.status["last_token_at"] = time.perf_counter()
            previous = self.status["last_content"] + content
            self.status["last_content"] = (full_content or previous)[-100:]

    def mark_idle(self) -> None:
        with self.status_lock:
            remaining = max(0, self.active_requests - 1)
            self.status["active_requests"] = remaining
            if remaining == 0:
                self.status["active"] = False
                self.status["phase"] = "idle"


class ModelRuntimeManager:
    """Own all loaded engines and route model keys/IDs to their runtime."""

    _PORT_FIELDS = {
        "llama_server": "llama_server_port",
        "mlx_vlm_server": "mlx_vlm_server_port",
    }

    def __init__(self, default_model: str | None = None) -> None:
        self._runtimes: dict[str, ModelRuntime] = {}
        self._aliases: dict[str, str] = {}
        self._loading: set[str] = set()
        self._reserved_ports: set[int] = set()
        self._manager_lock = threading.RLock()
        self._condition = threading.Condition(self._manager_lock)
        self.default_model = default_model

    def add(self, cfg: dict[str, Any], engine: Any, *, key: str | None = None) -> ModelRuntime:
        runtime_key = str(key or cfg["model"])
        model_id = str(cfg["model_id"])
        with self._manager_lock:
            for alias in {runtime_key, model_id}:
                existing_alias = self._aliases.get(alias)
                if existing_alias is not None:
                    raise ValueError(
                        f"Alias '{alias}' is already used by loaded model '{existing_alias}'."
                    )
            if runtime_key in self._runtimes:
                raise ValueError(
                    f"Model '{runtime_key}' is already loaded."
                )
            runtime = ModelRuntime(runtime_key, cfg, engine)
            self._runtimes[runtime_key] = runtime
            self._aliases[runtime_key] = runtime_key
            self._aliases[runtime.model_id] = runtime_key
            if self.default_model is None:
                self.default_model = runtime_key
            return runtime

    def load(self, model: str, **explicit: Any) -> tuple[ModelRuntime, bool]:
        from .config import build_config
        from .engine import load_llm

        with self._manager_lock:
            existing = self._resolve_unlocked(model)
            if existing is not None:
                if existing.state is not RuntimeState.READY:
                    raise RuntimeError(f"Model '{existing.key}' is not ready.")
                return existing, False
            if model in self._loading:
                raise RuntimeError(f"Model '{model}' is already loading.")
            cfg = build_config(model=model, **explicit)
            self._assign_private_port(cfg)
            field_name = self._PORT_FIELDS.get(str(cfg.get("backend")))
            reserved_port = int(cfg[field_name]) if field_name else None
            if reserved_port is not None:
                self._reserved_ports.add(reserved_port)
            self._loading.add(model)

        try:
            engine = load_llm(cfg)
            try:
                return self.add(cfg, engine, key=model), True
            except Exception:
                _close_engine(engine)
                raise
        finally:
            with self._manager_lock:
                self._loading.discard(model)
                if reserved_port is not None:
                    self._reserved_ports.discard(reserved_port)

    def resolve(self, model: str | None = None) -> ModelRuntime:
        target = model or self.default_model
        if not target:
            raise LookupError("No default model is configured.")
        with self._manager_lock:
            runtime = self._resolve_unlocked(str(target))
            if runtime is None:
                raise LookupError(f"Model '{target}' is not loaded.")
            return runtime

    @contextmanager
    def lease_runtime(self, runtime: ModelRuntime) -> Iterator[ModelRuntime]:
        """Keep a resolved runtime alive for the full duration of one request."""
        with self._condition:
            current = self._runtimes.get(runtime.key)
            if current is not runtime or runtime.state is not RuntimeState.READY:
                raise LookupError(f"Model '{runtime.key}' is no longer available.")
            runtime.active_requests += 1

        try:
            with runtime.admission:
                yield runtime
        finally:
            with self._condition:
                runtime.active_requests -= 1
                self._condition.notify_all()

    def _resolve_unlocked(self, model: str) -> ModelRuntime | None:
        key = self._aliases.get(model, model)
        return self._runtimes.get(key)

    def set_default(self, model: str) -> ModelRuntime:
        runtime = self.resolve(model)
        with self._manager_lock:
            self.default_model = runtime.key
        return runtime

    def reload(self, model: str, **explicit: Any) -> ModelRuntime:
        """Replace one idle runtime atomically, preserving it if loading fails."""
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
        new_engine = None
        try:
            cfg = build_config(model=current.key, **explicit)
            with self._manager_lock:
                self._assign_private_port(cfg)
            new_engine = load_llm(cfg)
            replacement = ModelRuntime(current.key, cfg, new_engine)
            with self._manager_lock:
                if self._runtimes.get(current.key) is not current:
                    raise RuntimeError(f"Model '{current.key}' changed while reloading.")
                for alias in {replacement.key, replacement.model_id}:
                    owner = self._aliases.get(alias)
                    if owner is not None and owner != current.key:
                        raise ValueError(
                            f"Alias '{alias}' is already used by loaded model '{owner}'."
                        )
                self._runtimes[current.key] = replacement
                for alias, key in list(self._aliases.items()):
                    if key == current.key:
                        self._aliases.pop(alias, None)
                self._aliases[current.key] = current.key
                self._aliases[replacement.model_id] = current.key
            _close_engine(current.engine)
            current.state = RuntimeState.STOPPED
            return replacement
        except Exception:
            if new_engine is not None:
                _close_engine(new_engine)
            with self._manager_lock:
                if self._runtimes.get(current.key) is current:
                    current.state = RuntimeState.READY
            raise

    def list(self) -> list[ModelRuntime]:
        with self._manager_lock:
            return list(self._runtimes.values())

    def unload(self, model: str) -> ModelRuntime:
        runtime = self.resolve(model)
        with self._manager_lock:
            if self._runtimes.get(runtime.key) is not runtime:
                raise LookupError(f"Model '{model}' is no longer loaded.")
            if runtime.state is not RuntimeState.READY:
                raise RuntimeError(f"Model '{runtime.key}' is not ready.")
            if len(self._runtimes) == 1:
                raise RuntimeError("Cannot unload the last resident model.")
            if runtime.active_requests:
                raise RuntimeError(f"Model '{runtime.key}' has an active request.")
            runtime.state = RuntimeState.DRAINING
            self._runtimes.pop(runtime.key, None)
            for alias, key in list(self._aliases.items()):
                if key == runtime.key:
                    self._aliases.pop(alias, None)
            if self.default_model == runtime.key:
                self.default_model = next(iter(self._runtimes), None)
        _close_engine(runtime.engine)
        runtime.state = RuntimeState.STOPPED
        return runtime

    def shutdown(self) -> None:
        with self._condition:
            runtimes = list(self._runtimes.values())
            for runtime in runtimes:
                runtime.state = RuntimeState.DRAINING
            self._runtimes.clear()
            self._aliases.clear()
            self.default_model = None
            while any(runtime.active_requests for runtime in runtimes):
                self._condition.wait()
        for runtime in runtimes:
            _close_engine(runtime.engine)
            runtime.state = RuntimeState.STOPPED

    def _assign_private_port(self, cfg: dict[str, Any]) -> None:
        field_name = self._PORT_FIELDS.get(str(cfg.get("backend")))
        if not field_name:
            return
        used = set(self._reserved_ports)
        for runtime in self._runtimes.values():
            for private_port_field in self._PORT_FIELDS.values():
                if runtime.cfg.get(private_port_field) is not None:
                    used.add(int(runtime.cfg[private_port_field]))
        port = int(cfg.get(field_name) or 0)
        while port in used:
            port += 1
        cfg[field_name] = port
