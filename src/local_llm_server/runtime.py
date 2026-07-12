"""Lifecycle, routing, and concurrency ownership for resident model engines."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


_BACKEND_CONFIG_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "llama_cpp": (
        "ctx_size", "n_gpu_layers", "n_threads", "n_batch", "n_ubatch",
        "timeout", "offload_kqv", "flash_attn", "use_mmap", "enable_thinking",
        "show_thinking",
    ),
    "llama_server": ("ctx_size", "timeout", "enable_thinking", "show_thinking"),
    "mlx": ("enable_thinking", "show_thinking"),
    "mlx_vlm_server": ("timeout",),
}


def config_capabilities_for_backend(backend: str) -> list[str]:
    """Return only settings that the current engine implementation consumes."""
    return list(_BACKEND_CONFIG_CAPABILITIES.get(backend, ()))


def new_runtime_status(model_id: str) -> dict[str, Any]:
    return {
        "active": False,
        "active_requests": 0,
        "phase": "idle",
        "tokens_generated": 0,
        "max_tokens": 0,
        "started_at": 0.0,
        "last_token_at": 0.0,
        "tokens_per_second": 0.0,
        "model": model_id,
        "last_content": "",
    }


@dataclass
class ModelRuntime:
    key: str
    cfg: dict[str, Any]
    engine: Any
    lock: threading.Lock = field(default_factory=threading.Lock)
    status_lock: threading.Lock = field(default_factory=threading.Lock)
    status: dict[str, Any] = field(default_factory=dict)
    loaded_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.status:
            self.status = new_runtime_status(str(self.cfg["model_id"]))

    @property
    def model_id(self) -> str:
        return str(self.cfg["model_id"])

    def snapshot_status(self) -> dict[str, Any]:
        with self.status_lock:
            result = dict(self.status)
        if result["active"] and result["phase"] == "generating" and result["tokens_generated"] > 0:
            elapsed = time.perf_counter() - result["started_at"]
            if elapsed > 0:
                result["tokens_per_second"] = result["tokens_generated"] / elapsed
        result["key"] = self.key
        result["backend"] = getattr(self.engine, "backend", self.cfg.get("backend", "unknown"))
        result["loaded_at"] = self.loaded_at
        return result


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
        self.default_model = default_model

    def add(self, cfg: dict[str, Any], engine: Any, *, key: str | None = None) -> ModelRuntime:
        runtime_key = str(key or cfg["model"])
        with self._manager_lock:
            if runtime_key in self._runtimes:
                raise ValueError(f"Model '{runtime_key}' is already loaded.")
            existing_alias = self._aliases.get(str(cfg["model_id"]))
            if existing_alias is not None:
                raise ValueError(
                    f"Model ID '{cfg['model_id']}' is already used by loaded model '{existing_alias}'."
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
                if hasattr(engine, "shutdown"):
                    engine.shutdown()
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
        if not current.lock.acquire(blocking=False):
            raise RuntimeError(f"Model '{current.key}' has an active request.")
        new_engine = None
        try:
            cfg = build_config(model=current.key, **explicit)
            with self._manager_lock:
                self._assign_private_port(cfg)
            new_engine = load_llm(cfg)
            replacement = ModelRuntime(current.key, cfg, new_engine)
            with self._manager_lock:
                self._runtimes[current.key] = replacement
                for alias, key in list(self._aliases.items()):
                    if key == current.key:
                        self._aliases.pop(alias, None)
                self._aliases[current.key] = current.key
                self._aliases[replacement.model_id] = current.key
            if hasattr(current.engine, "shutdown"):
                current.engine.shutdown()
            return replacement
        except Exception:
            if new_engine is not None and hasattr(new_engine, "shutdown"):
                new_engine.shutdown()
            raise
        finally:
            current.lock.release()

    def list(self) -> list[ModelRuntime]:
        with self._manager_lock:
            return list(self._runtimes.values())

    def unload(self, model: str) -> ModelRuntime:
        runtime = self.resolve(model)
        if not runtime.lock.acquire(blocking=False):
            raise RuntimeError(f"Model '{runtime.key}' has an active request.")
        try:
            with self._manager_lock:
                if len(self._runtimes) == 1:
                    raise RuntimeError("Cannot unload the last resident model.")
                self._runtimes.pop(runtime.key, None)
                for alias, key in list(self._aliases.items()):
                    if key == runtime.key:
                        self._aliases.pop(alias, None)
                if self.default_model == runtime.key:
                    self.default_model = next(iter(self._runtimes), None)
            if hasattr(runtime.engine, "shutdown"):
                runtime.engine.shutdown()
            return runtime
        finally:
            runtime.lock.release()

    def shutdown(self) -> None:
        with self._manager_lock:
            runtimes = list(self._runtimes.values())
            self._runtimes.clear()
            self._aliases.clear()
            self.default_model = None
        for runtime in runtimes:
            if hasattr(runtime.engine, "shutdown"):
                runtime.engine.shutdown()

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
