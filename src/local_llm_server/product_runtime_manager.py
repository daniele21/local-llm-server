"""Product runtime manager with explicit configured-vs-resident default semantics."""
from __future__ import annotations

from typing import Any

from .resource_manager import ResourceManager
from .runtime import ModelRuntime, ModelRuntimeManager, RuntimeState


def _close_engine(engine: Any) -> None:
    close = getattr(engine, "close", None) or getattr(engine, "shutdown", None)
    if close is not None:
        close()


class ProductRuntimeManager(ModelRuntimeManager):
    """Runtime manager that permits a healthy zero-resident product state.

    ``configured_default_model`` is the desired/default identity from product
    configuration. ``default_model`` remains the currently routable resident
    default and may therefore be ``None`` while the server is healthy but cold.
    """

    def __init__(
        self,
        default_model: str | None = None,
        *,
        resource_manager: ResourceManager | None = None,
    ) -> None:
        # The base manager's default_model means "currently routable resident
        # default". Do not preload the configured identity into that field: a
        # product may start cold or load a non-default runtime first.
        super().__init__(
            default_model=None,
            resource_manager=resource_manager,
        )
        self.configured_default_model = default_model

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
        runtime = super().add(cfg, engine, key=key)
        with self._manager_lock:
            configured = self.configured_default_model
            if configured is None:
                self.configured_default_model = runtime.key
                self.default_model = runtime.key
            elif configured in {runtime.key, runtime.model_id}:
                # Restore the desired route when its runtime becomes resident.
                self.default_model = runtime.key
            elif previous_resident_default is None:
                # Loading a different runtime while the configured default is
                # cold must not silently replace the configured route.
                self.default_model = None
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

    def set_default(self, model: str) -> ModelRuntime:
        runtime = super().set_default(model)
        with self._manager_lock:
            self.configured_default_model = runtime.key
        return runtime

    def unload(self, model: str) -> ModelRuntime:
        """Unload any idle runtime, including the last resident runtime."""
        runtime = self.resolve(model)
        with self._manager_lock:
            if self._runtimes.get(runtime.key) is not runtime:
                raise LookupError(f"Model '{model}' is no longer loaded.")
            if runtime.state is not RuntimeState.READY:
                raise RuntimeError(f"Model '{runtime.key}' is not ready.")
            if runtime.active_requests:
                raise RuntimeError(
                    f"Model '{runtime.key}' has an active request."
                )

            runtime.state = RuntimeState.DRAINING
            self._runtimes.pop(runtime.key, None)
            for alias, key in list(self._aliases.items()):
                if key == runtime.key:
                    self._aliases.pop(alias, None)

            if self.default_model == runtime.key:
                self.default_model = next(iter(self._runtimes), None)

        _close_engine(runtime.engine)
        self._release_runtime_load(runtime.resource_reservation_id)
        runtime.state = RuntimeState.STOPPED
        return runtime

    def shutdown(self) -> None:
        """Stop all resident runtimes while retaining configured identity."""
        configured = self.configured_default_model
        super().shutdown()
        self.configured_default_model = configured
