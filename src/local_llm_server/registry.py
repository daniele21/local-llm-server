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

    return {
        "models_dir": models_dir,
        "defaults": defaults,
        "models": models,
        "default_model": default_model,
        "startup_models": list(user.get("startup_models") or builtin.get("startup_models") or []),
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}
