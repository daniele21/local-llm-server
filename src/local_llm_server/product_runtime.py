"""High-level runtime bootstrap used by supported product entrypoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .resource_policy import (
    ResourcePolicySettings,
    build_resource_manager,
)
from .runtime import ModelRuntimeManager


@dataclass(frozen=True, slots=True)
class ProductRuntimeBootstrap:
    manager: ModelRuntimeManager
    cfg: dict[str, Any]
    engine: Any
    resource_policy: ResourcePolicySettings


def bootstrap_product_runtimes(
    *,
    model: str | None = None,
    model_path: str | None = None,
    models: Sequence[str] | None = None,
    default_model: str | None = None,
    explicit: Mapping[str, Any] | None = None,
    resource_policy: ResourcePolicySettings | None = None,
) -> ProductRuntimeBootstrap:
    """Load all startup runtimes through ResourceManager-aware lifecycle code."""
    from .registry import load_registry

    registry = load_registry()
    overrides = dict(explicit or {})
    policy = resource_policy or ResourcePolicySettings.from_environment()
    resource_manager = build_resource_manager(policy)

    startup_models = list(models or [])
    if startup_models and model_path is not None:
        raise ValueError("model_path cannot be combined with multiple startup models")

    selected_default = (
        default_model
        or model
        or (startup_models[0] if startup_models else None)
        or str(registry["default_model"])
    )
    if startup_models:
        if selected_default not in startup_models:
            startup_models.insert(0, selected_default)
    else:
        startup_models = [selected_default]

    manager = ModelRuntimeManager(
        default_model=selected_default,
        resource_manager=resource_manager,
    )
    try:
        for model_key in startup_models:
            per_model = dict(overrides)
            if model_key == selected_default and model_path is not None:
                per_model["model_path"] = model_path
            if model_key != selected_default:
                # Managed subprocess backends receive collision-free private
                # ports from ModelRuntimeManager; do not force the same explicit
                # default port onto every resident model.
                per_model.pop("llama_server_port", None)
                per_model.pop("mlx_vlm_server_port", None)
            manager.load(model_key, **per_model)
    except Exception:
        manager.shutdown()
        raise

    runtime = manager.resolve(selected_default)
    return ProductRuntimeBootstrap(
        manager=manager,
        cfg=runtime.cfg,
        engine=runtime.engine,
        resource_policy=policy,
    )


def effective_policy_for_manager(
    manager: ModelRuntimeManager,
) -> ResourcePolicySettings:
    """Describe the policy actually enforced by an existing manager."""
    resource_manager = manager.resource_manager
    if resource_manager is None:
        return ResourcePolicySettings()
    budget = resource_manager.budget
    return ResourcePolicySettings(
        memory_limit_bytes=budget.limit_bytes,
        headroom_bytes=budget.headroom_bytes,
    )
