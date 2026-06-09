"""
config.py — resolve final inference configuration.

Priority (highest → lowest):
  1. Explicit kwargs / CLI flags
  2. Environment variables
  3. Registry entry params
  4. Registry defaults section
  5. Hardcoded fallbacks
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .registry import load_registry

# ── Hardcoded fallbacks ────────────────────────────────────────────────────────
_FALLBACKS: dict[str, Any] = {
    "host": "127.0.0.1",
    "port": 1235,
    "ctx_size": 4096,
    "n_gpu_layers": 0,
    "n_threads": 8,
    "n_batch": 512,
    "n_ubatch": 512,
    "offload_kqv": True,
    "flash_attn": True,
    "use_mmap": True,
    "chat_format": None,
    "timeout": 1200,
    "force_json": False,
    "enable_thinking": False,
    "show_thinking": False,
    "verbose": False,
    "no_download": False,
    "default_temperature": 0.0,
    "backend": "llama_cpp",
}

# ── Env-var names ──────────────────────────────────────────────────────────────
_ENV_MAP: dict[str, str] = {
    "host": "LOCAL_LLM_HOST",
    "port": "LOCAL_LLM_PORT",
    "ctx_size": "LOCAL_LLM_CTX_SIZE",
    "n_gpu_layers": "LOCAL_LLM_N_GPU_LAYERS",
    "n_threads": "LOCAL_LLM_N_THREADS",
    "n_batch": "LOCAL_LLM_N_BATCH",
    "n_ubatch": "LOCAL_LLM_N_UBATCH",
    "chat_format": "LOCAL_LLM_CHAT_FORMAT",
    "timeout": "LOCAL_LLM_TIMEOUT",
    "force_json": "LOCAL_LLM_FORCE_JSON",
    "enable_thinking": "LOCAL_LLM_ENABLE_THINKING",
    "show_thinking": "LOCAL_LLM_SHOW_THINKING",
    "verbose": "LOCAL_LLM_VERBOSE",
    "backend": "LOCAL_LLM_BACKEND",
}

_BOOL_ENV = {"force_json", "enable_thinking", "show_thinking", "verbose", "offload_kqv", "flash_attn", "use_mmap"}
_INT_ENV = {"port", "ctx_size", "n_gpu_layers", "n_threads", "n_batch", "n_ubatch", "timeout"}


def build_config(
    model: str | None = None,
    model_path: str | None = None,
    **explicit: Any,
) -> dict[str, Any]:
    """
    Return a fully resolved config dict ready to pass to load_llm() and LocalLLMServer.

    Parameters
    ----------
    model:      Registry key (e.g. "qwen3-8b"). If None, uses default_model.
    model_path: Direct path to a .gguf file. If set, skips registry path resolution.
    **explicit: Any config key explicitly set by the caller (CLI flags / library API).
    """
    registry = load_registry()
    models_dir: Path = registry["models_dir"]

    # Resolve model key
    if model is None:
        model = registry["default_model"]

    entry: dict[str, Any] = registry["models"].get(model) or {}
    reg_params: dict[str, Any] = {
        **registry.get("defaults", {}),
        **entry.get("params", {}),
    }

    # Resolve backend
    backend = explicit.get("backend") or entry.get("backend") or os.getenv("LOCAL_LLM_BACKEND") or reg_params.get("backend") or "llama_cpp"

    # Resolve model_path
    if model_path is None:
        if backend == "mlx":
            model_path = entry.get("path") or entry.get("model_id") or model
        else:
            filename = entry.get("filename", f"{model}.gguf")
            model_path = str(models_dir / filename)

    model_id: str = entry.get("model_id", model)
    download_url: str = entry.get("url", "")

    cfg: dict[str, Any] = {}

    for key, fallback in _FALLBACKS.items():
        # 1. Explicit caller value
        if key in explicit and explicit[key] is not None:
            cfg[key] = explicit[key]
            continue

        # 2. Environment variable
        env_name = _ENV_MAP.get(key)
        env_val = os.getenv(env_name, "") if env_name else ""
        if env_val:
            if key in _INT_ENV:
                cfg[key] = int(env_val)
            elif key in _BOOL_ENV:
                cfg[key] = env_val.lower() in {"1", "true", "yes", "on"}
            else:
                cfg[key] = env_val
            continue

        # 3. Registry param
        if key in reg_params:
            cfg[key] = reg_params[key]
            continue

        # 4. Hardcoded fallback
        cfg[key] = fallback

    cfg["model"] = model
    cfg["model_id"] = model_id
    cfg["model_path"] = model_path
    cfg["download_url"] = download_url
    cfg["models_dir"] = models_dir
    cfg["backend"] = backend

    return cfg
