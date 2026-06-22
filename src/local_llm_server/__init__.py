"""local_llm_server — public API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .audio import audio_to_base64, prepare_audio, prepare_audio_message
from .client import LocalLLMClient
from .server import run_server

__all__ = [
    "run_server",
    "serve",
    "download_model",
    "list_models",
    "ServerHandle",
    "LocalLLMClient",
    "prepare_audio",
    "audio_to_base64",
    "prepare_audio_message",
]


def serve(
    model: str | None = None,
    model_path: str | None = None,
    host: str = "127.0.0.1",
    port: int = 1235,
    background: bool = False,
    no_download: bool = False,
    **kwargs,
) -> "ServerHandle | None":
    """
    Start the local LLM server.

    Parameters
    ----------
    model:       Key from the built-in or user registry (e.g. "qwen3-8b").
    model_path:  Direct path to a .gguf file (bypasses registry).
    host:        Bind address.
    port:        HTTP port.
    background:  If True, starts the server in a background thread and
                 returns a ServerHandle with a .shutdown() method.
                 If False (default), blocks until SIGINT/SIGTERM.
    no_download: Raise an error instead of auto-downloading a missing model.
    **kwargs:    Extra inference params (ctx_size, n_gpu_layers, …).
    """
    import os
    import threading
    import uvicorn
    from .config import build_config
    from .engine import load_llm
    from .server import app

    cfg = build_config(
        model=model,
        model_path=model_path,
        host=host,
        port=port,
        no_download=no_download,
        **kwargs,
    )
    llm = load_llm(cfg)
    app.state.cfg = cfg
    app.state.llm = llm
    app.state.generation_lock = threading.Lock()
    app.state.shutdown = False
    app.state.terminal_cwd = os.getcwd()
    app.state.current_status = {
        "active": False,
        "phase": "idle",
        "tokens_generated": 0,
        "max_tokens": 0,
        "started_at": 0.0,
        "last_token_at": 0.0,
        "tokens_per_second": 0.0,
        "model": cfg["model_id"],
        "last_content": "",
    }

    config = uvicorn.Config(
        app,
        host=cfg["host"],
        port=cfg["port"],
        log_level="warning" if not cfg.get("verbose", False) else "info",
    )
    server = uvicorn.Server(config)

    if background:
        t = threading.Thread(target=server.run, daemon=True)
        t.start()
        return ServerHandle(server, thread=t, llm=llm)

    import signal as _signal

    def _shutdown(signum, _frame):
        server.should_exit = True

    _signal.signal(_signal.SIGINT, _shutdown)
    _signal.signal(_signal.SIGTERM, _shutdown)
    try:
        server.run()
    finally:
        if hasattr(llm, "shutdown"):
            llm.shutdown()
    return None


def download_model(model: str) -> None:
    """Download a model from the registry if not already on disk."""
    from .registry import load_registry
    from .downloader import ensure_model

    registry = load_registry()
    models_dir = registry["models_dir"]
    entry = registry["models"].get(model)
    if entry is None:
        raise ValueError(f"Model '{model}' not found in registry. Run 'local-llm models' to list available models.")
    ensure_model(
        url=entry.get("url", ""),
        dest=models_dir / entry["filename"],
    )


def list_models() -> list[dict]:
    """Return the list of models from the merged registry."""
    from .registry import load_registry

    registry = load_registry()
    models_dir = registry["models_dir"]
    result = []
    for key, entry in registry["models"].items():
        path = models_dir / entry["filename"]
        lmstudio_path = None
        if entry.get("lmstudio_path"):
            lmstudio_path = (
                Path.home()
                / ".lmstudio"
                / "models"
                / str(entry["lmstudio_path"])
                / str(entry["filename"])
            )
        resolved_path = lmstudio_path if lmstudio_path and lmstudio_path.exists() else path
        result.append(
            {
                "key": key,
                "model_id": entry.get("model_id", key),
                "size_gb": entry.get("size_gb"),
                "tags": entry.get("tags", []),
                "backend": entry.get("backend", "llama_cpp"),
                "multimodal": bool(entry.get("multimodal", False)),
                "modalities": entry.get("modalities", []),
                "downloaded": resolved_path.exists(),
                "path": str(resolved_path),
            }
        )
    return result


class ServerHandle:
    def __init__(self, server: Any, thread: Any | None = None, llm: Any | None = None):
        self._server = server
        self._thread = thread
        self._llm = llm

    def shutdown(self) -> None:
        self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=10)
        if self._llm is not None and hasattr(self._llm, "shutdown"):
            self._llm.shutdown()
