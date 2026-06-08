"""
engine.py — load a llama-cpp-python Llama instance from a resolved config dict.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .downloader import ensure_model

logger = logging.getLogger("local-llm.engine")


def load_llm(cfg: dict[str, Any]) -> Any:
    """
    Ensure the model file is present (auto-download if needed) and load it
    into a llama_cpp.Llama instance.

    Parameters
    ----------
    cfg : dict returned by config.build_config()
    """
    model_path = Path(cfg["model_path"]).expanduser()

    ensure_model(
        url=cfg.get("download_url", ""),
        dest=model_path,
        no_download=cfg.get("no_download", False),
    )

    try:
        from llama_cpp import Llama
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: llama-cpp-python. "
            "Install it with: pip install llama-cpp-python"
        ) from exc

    kwargs: dict[str, Any] = {
        "model_path": str(model_path),
        "n_ctx": cfg["ctx_size"],
        "n_batch": cfg["n_batch"],
        "n_ubatch": cfg["n_ubatch"],
        "n_gpu_layers": cfg["n_gpu_layers"],
        "n_threads": cfg["n_threads"],
        "offload_kqv": cfg["offload_kqv"],
        "flash_attn": cfg["flash_attn"],
        "use_mmap": cfg["use_mmap"],
        "verbose": cfg["verbose"],
    }

    if cfg.get("chat_format"):
        kwargs["chat_format"] = cfg["chat_format"]

    logger.info("Loading model: %s", model_path)
    logger.info(
        "Model configuration: %s",
        json.dumps(
            {k: v for k, v in kwargs.items() if k != "model_path"},
            indent=2,
        ),
    )

    llm = Llama(**kwargs)
    logger.info("Model loaded.")
    return llm
