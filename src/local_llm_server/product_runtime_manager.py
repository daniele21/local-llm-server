"""Product runtime manager with explicit configured-vs-resident default semantics."""
from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .resource_manager import ResourceManager
from .runtime import ModelRuntime, ModelRuntimeManager, RuntimeState
from .stream_contract import ensure_stream_contract


class ProductRuntimeManager(ModelRuntimeManager):
    """Runtime manager that permits a healthy zero-resident product state.

    ``configured_default_model`` is the desired/default identity from product
    configuration. ``default_model`` remains the currently routable resident
    default and may therefore be ``None`` while the server is healthy but cold.

    Residency pinning is an explicit policy signal for future automatic
    eviction. A pinned runtime may still be manually unloaded; pinning only
    removes it from automatic-eviction candidate sets.
    """

    def __init__(
        self,
        default_model: str | None = None,
        *,
        resource_manager: ResourceManager | None = None,
    ) -> None:
        super().__init__(
            default_model=None,
            resource_manager=resource_manager,
        )
        self.configured_default_model = default_model
        self._pinned_runtime_keys: set[str] = set()
        self._last_used_at_monotonic: dict[str, float] = {}

    @property
    def cold(self) -> bool:
        return len(self.list()) == 0

    def add(
        self,
        cfg: dict[str, Any],
        engine: Any,
        *,
        key: str | None = None,
    ) -> ModelRuntime:
        previous_resident_default = self.default_model
        runtime = super().add(cfg, ensure_stream_contract(engine), key=key)
        with self._manager_lock:
            self._last_used_at_monotonic[runtime.key] = time.monotonic()
            configured = self.configured_default_model
            if configured is None:
                self.configured_default_model = runtime.key
                self.default_model = runtime.key
            elif configured in {runtime.key, runtime.model_id}:
                self.default_model = runtime.key
            elif previous_resident_default is None:
                self.default_model = None

        # Capture once after the runtime is resident. The helper is deliberately
        # conservative and returns None unless artifact SHA + backend version
        # are both strong enough for an evidence-grade identity.
        from .runtime_identity_capture import capture_verified_runtime_identity

        capture_verified_runtime_identity(runtime)
        return runtime

    def resolve(self, model: str | None = None) -> ModelRuntime:
        if model is None and self.default_model is None:
            configured = self.configured_default_model
            if configured:
                raise LookupError(
                    f"Configured default model '{configured}' is not resident."
                )
            raise LookupError("No resident default model is available.")
        return super().resolve(model)

    @contextmanager
    def lease_runtime(self, runtime: ModelRuntime) -> Iterator[ModelRuntime]:
        """Lease a runtime and update LRU recency only after the lease ends."""
        try:
            with super().lease_runtime(runtime) as leased:
                yield leased
        finally:
            with self._manager_lock:
                if self._runtimes.get(runtime.key) is runtime:
                    self._last_used_at_monotonic[runtime.key] = time.monotonic()

    def reload(self, model: str, **explicit: Any) -> ModelRuntime:
        replacement = super().reload(model, **explicit)
        replacement.engine = ensure_stream_contract(replacement.engine)
        with self._manager_lock:
            self._last_used_at_monotonic[replacement.key] = time.monotonic()
        return replacement

    def set_default(self, model: str) -> ModelRuntime:
        runtime = super().set_default(model)
        with self._manager_lock:
            self.configured_default_model = runtime.key
        return runtime

    def set_pinned(self, model: str, pinned: bool) -> ModelRuntime:
        """Set automatic-eviction pin state for one resident runtime."""
        runtime = self.resolve(model)
        with self._manager_lock:
            if self._runtimes.get(runtime.key) is not runtime:
                raise LookupError(f"Model '{model}' is no longer loaded.")
            if pinned:
                self._pinned_runtime_keys.add(runtime.key)
            else:
                self._pinned_runtime_keys.discard(runtime.key)
        return runtime

    def is_pinned(self, model: str) -> bool:
        runtime = self.resolve(model)
        with self._manager_lock:
            return runtime.key in self._pinned_runtime_keys

    def residency_policy_snapshot(self) -> dict[str, Any]:
        """Return public-safe residency policy state for current runtimes.

        ``evictable`` means only that the runtime is an eligible policy
        candidate right now. It is not evidence that unload will reclaim host
        memory; reclamation remains a separate observed-evidence concern.
        """
        now = time.monotonic()
        with self._manager_lock:
            runtimes = list(self._runtimes.values())
            pinned = set(self._pinned_runtime_keys)
            last_used = dict(self._last_used_at_monotonic)
            configured_default = self.configured_default_model
            resident_default = self.default_model

        return {
            "configured_default_model": configured_default,
            "resident_default_model": resident_default,
            "cold": len(runtimes) == 0,
            "runtimes": [
                {
                    "key": runtime.key,
                    "model": runtime.model_id,
                    "state": runtime.state.value,
                    "active_requests": runtime.active_requests,
                    "pinned": runtime.key in pinned,
                    "is_resident_default": runtime.key == resident_default,
                    "last_used_age_seconds": max(
                        0.0,
                        now - last_used.get(runtime.key, now),
                    ),
                    "evictable": (
                        runtime.key not in pinned
                        and runtime.state is RuntimeState.READY
                        and runtime.active_requests == 0
                    ),
                }
                for runtime in runtimes
            ],
        }

    def unload(self, model: str) -> ModelRuntime:
        """Unload any idle runtime, including the last resident runtime."""
        runtime = super()._unload(model, allow_last=True)
        with self._manager_lock:
            self._pinned_runtime_keys.discard(runtime.key)
            self._last_used_at_monotonic.pop(runtime.key, None)
        return runtime

    def shutdown(self, *, timeout_seconds: float = 30.0) -> None:
        """Stop resident runtimes while retaining configured product identity."""
        configured = self.configured_default_model
        try:
            super().shutdown(timeout_seconds=timeout_seconds)
        finally:
            # Keep policy bookkeeping only for runtimes whose teardown failed and
            # therefore remain canonically owned/accounted by the base manager.
            with self._manager_lock:
                resident = set(self._runtimes)
                self._pinned_runtime_keys.intersection_update(resident)
                self._last_used_at_monotonic = {
                    key: value
                    for key, value in self._last_used_at_monotonic.items()
                    if key in resident
                }
            self.configured_default_model = configured
