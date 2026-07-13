"""
registry.py — load and merge the built-in + user model registry.

Resolution order (lowest → highest priority):
  1. Built-in registry  (src/local_llm_server/models_registry.yaml)
  2. User registry      (~/.local-llm/models.yaml)

The result is a dict with keys:
  models_dir: Path
  defaults:   dict
  models:     dict[str, dict]
  default_model: str
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_BUILTIN_REGISTRY = Path(__file__).parent / "models_registry.yaml"
_USER_REGISTRY = Path.home() / ".local-llm" / "models.yaml"
_SUPPORTED_BACKENDS = {"llama_cpp", "gguf", "mlx", "llama_server", "mlx_vlm_server"}
_VALID_MODALITIES = {"text", "image", "audio"}


def load_registry() -> dict[str, Any]:
    """Return the merged registry as a plain dict."""
    builtin = _load_yaml(_BUILTIN_REGISTRY)
    user = _load_yaml(_USER_REGISTRY) if _USER_REGISTRY.exists() else {}

    # Merge models: user entries override or extend built-in ones
    models: dict[str, Any] = dict(builtin.get("models") or {})
    for key, entry in (user.get("models") or {}).items():
        if key in models:
            # Deep-merge params
            merged = dict(models[key])
            merged["params"] = {**merged.get("params", {}), **entry.get("params", {})}
            for k, v in entry.items():
                if k != "params":
                    merged[k] = v
            models[key] = merged
        else:
            models[key] = entry

    # Resolve models_dir
    raw_dir = user.get("models_dir") or builtin.get("models_dir") or "~/.local-llm/models"
    models_dir = Path(str(raw_dir)).expanduser().resolve()

    defaults = {**builtin.get("defaults", {}), **user.get("defaults", {})}

    default_model: str = (
        user.get("default_model")
        or builtin.get("default_model")
        or (next(iter(models)) if models else "")
    )

    registry = {
        "models_dir": models_dir,
        "defaults": defaults,
        "models": models,
        "default_model": default_model,
        "startup_models": list(user.get("startup_models") or builtin.get("startup_models") or []),
    }
    validate_registry(registry)
    return registry


def validate_registry(registry: dict[str, Any]) -> None:
    """Raise a clear error when the merged registry violates runtime invariants."""
    errors: list[str] = []
    models = registry.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError("Registry validation failed:\n- models must be a non-empty mapping.")

    aliases: dict[str, str] = {}
    for key, entry in models.items():
        label = f"models.{key}"
        if not isinstance(key, str) or not key.strip():
            errors.append("model keys must be non-empty strings")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{label} must be a mapping")
            continue

        model_id = entry.get("model_id", key)
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append(f"{label}.model_id must be a non-empty string")
        for alias in {key, str(model_id)}:
            owner = aliases.get(alias)
            if owner is not None and owner != key:
                errors.append(f"alias '{alias}' is shared by '{owner}' and '{key}'")
            aliases[alias] = key

        backend = str(entry.get("backend") or registry.get("defaults", {}).get("backend") or "llama_cpp")
        if backend not in _SUPPORTED_BACKENDS:
            errors.append(f"{label}.backend '{backend}' is unsupported")

        params = entry.get("params", {})
        if not isinstance(params, dict):
            errors.append(f"{label}.params must be a mapping")
            params = {}
        for field_name in (
            "ctx_size", "max_kv_size", "max_concurrent_requests",
            "llama_server_port", "mlx_vlm_server_port", "startup_timeout",
        ):
            if field_name in params:
                value = params[field_name]
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    errors.append(f"{label}.params.{field_name} must be a positive integer")

        thinking_mode = entry.get("thinking_mode", "none")
        if thinking_mode not in {"none", "switchable", "always"}:
            errors.append(
                f"{label}.thinking_mode must be 'none', 'switchable', or 'always'"
            )

        modalities = entry.get("modalities", ["text"])
        if not isinstance(modalities, list) or not modalities:
            errors.append(f"{label}.modalities must be a non-empty list")
        elif not set(modalities).issubset(_VALID_MODALITIES):
            errors.append(f"{label}.modalities contains an unsupported value")
        elif "text" not in modalities:
            errors.append(f"{label}.modalities must include 'text'")

        multimodal = entry.get("multimodal", False)
        if not isinstance(multimodal, bool):
            errors.append(f"{label}.multimodal must be a boolean")
        elif multimodal != (isinstance(modalities, list) and any(mode != "text" for mode in modalities)):
            errors.append(f"{label}.multimodal must match its declared modalities")

        has_model_source = bool(entry.get("path") or entry.get("filename") or entry.get("model_id"))
        if backend in {"llama_cpp", "gguf", "llama_server", "mlx", "mlx_vlm_server"} and not has_model_source:
            errors.append(f"{label} needs path, filename, or model_id")
        if backend == "mlx_vlm_server" and not (entry.get("path") or entry.get("model_id")):
            errors.append(f"{label} with mlx_vlm_server needs path or model_id")
        if backend == "llama_server" and multimodal and not (
            entry.get("mmproj_filename") or params.get("mmproj_path")
        ):
            errors.append(f"{label} multimodal llama_server needs mmproj_filename or params.mmproj_path")

    default_model = registry.get("default_model")
    if default_model not in models:
        errors.append(f"default_model '{default_model}' is not present in models")
    startup_models = registry.get("startup_models", [])
    if not isinstance(startup_models, list) or any(model not in models for model in startup_models):
        errors.append("startup_models must contain only registered model keys")

    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Registry validation failed:\n{formatted}")


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}
