"""local_llm_server — public API."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .audio import audio_to_base64, prepare_audio, prepare_audio_message
from .client import LocalLLMClient
from .vision import image_to_data_url, prepare_image_message

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
    "image_to_data_url",
    "prepare_image_message",
]


def run_server(*args: Any, **kwargs: Any) -> None:
    """Start the HTTP server without importing FastAPI during package import."""
    from .server import run_server as _run_server

    _run_server(*args, **kwargs)


def serve(
    model: str | None = None,
    model_path: str | None = None,
    models: list[str] | None = None,
    default_model: str | None = None,
    host: str = "127.0.0.1",
    port: int = 1235,
    background: bool = False,
    no_download: bool = False,
    enable_admin_api: bool = False,
    cors_origins: list[str] | None = None,
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
    enable_admin_api: Register model-management and log-stream endpoints.
    cors_origins: Browser origins allowed to call the API. Disabled by default.
    **kwargs:    Extra inference params (ctx_size, n_gpu_layers, …).
    """
    import threading
    import uvicorn
    from .config import build_config
    from .engine import load_llm
    from .server import ServerSettings, configure_runtime, create_app
    from .runtime import ModelRuntimeManager

    startup_models = list(models or [])
    if startup_models:
        selected_default = default_model or model or startup_models[0]
        if selected_default not in startup_models:
            startup_models.insert(0, selected_default)
        manager = ModelRuntimeManager(default_model=selected_default)
        try:
            for model_key in startup_models:
                manager.load(
                    model_key,
                    host=host,
                    port=port,
                    no_download=no_download,
                    **kwargs,
                )
        except Exception:
            manager.shutdown()
            raise
        default_runtime = manager.resolve()
        cfg, llm = default_runtime.cfg, default_runtime.engine
    else:
        cfg = build_config(
            model=model,
            model_path=model_path,
            host=host,
            port=port,
            no_download=no_download,
            **kwargs,
        )
        llm = load_llm(cfg)
        manager = ModelRuntimeManager(default_model=str(cfg["model"]))
        manager.add(cfg, llm)
    application = create_app(
        settings=ServerSettings(
            enable_admin_api=enable_admin_api,
            cors_origins=tuple(cors_origins or ()),
        )
    )
    configure_runtime(cfg, llm, manager, target_app=application)

    config = uvicorn.Config(
        application,
        host=cfg["host"],
        port=cfg["port"],
        log_level="warning" if not cfg.get("verbose", False) else "info",
    )
    server = uvicorn.Server(config)

    if background:
        t = threading.Thread(target=server.run, daemon=True)
        t.start()
        return ServerHandle(server, thread=t, manager=manager)

    import signal as _signal

    def _shutdown(signum, _frame):
        server.should_exit = True

    _signal.signal(_signal.SIGINT, _shutdown)
    _signal.signal(_signal.SIGTERM, _shutdown)
    try:
        server.run()
    finally:
        manager.shutdown()
    return None


def download_model(model: str) -> None:
    """Download a model from the registry if not already on disk."""
    from .registry import load_registry
    from .downloader import download_huggingface_snapshot, ensure_model

    registry = load_registry()
    models_dir = registry["models_dir"]
    entry = registry["models"].get(model)
    if entry is None:
        raise ValueError(f"Model '{model}' not found in registry. Run 'local-llm models' to list available models.")
    if entry.get("path"):
        path = Path(str(entry["path"])).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Local model path not found: {path}")
        return
    if not entry.get("filename") and entry.get("model_id"):
        download_huggingface_snapshot(str(entry["model_id"]))
        return
    ensure_model(
        url=entry.get("url", ""),
        dest=models_dir / entry["filename"],
    )
    if entry.get("mmproj_filename"):
        ensure_model(
            url=entry.get("mmproj_url", ""),
            dest=models_dir / entry["mmproj_filename"],
        )


def list_models() -> list[dict]:
    """Return the list of models from the merged registry."""
    from .registry import load_registry
    from .downloader import is_huggingface_snapshot_cached

    registry = load_registry()
    models_dir = registry["models_dir"]
    result = []
    for key, entry in registry["models"].items():
        if entry.get("path"):
            path = Path(str(entry["path"])).expanduser()
            downloaded = path.exists()
        elif entry.get("filename"):
            path = models_dir / entry["filename"]
            downloaded = path.exists()
        else:
            path = Path(str(entry.get("model_id", key)))
            downloaded = is_huggingface_snapshot_cached(str(entry.get("model_id", key)))
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
        if entry.get("path") or entry.get("filename"):
            downloaded = resolved_path.exists()
        mmproj_path = None
        if entry.get("mmproj_filename"):
            mmproj_path = models_dir / entry["mmproj_filename"]
            lmstudio_mmproj = None
            if entry.get("lmstudio_path"):
                lmstudio_mmproj = (
                    Path.home() / ".lmstudio" / "models" / str(entry["lmstudio_path"])
                    / str(entry["mmproj_filename"])
                )
            if lmstudio_mmproj and lmstudio_mmproj.exists():
                mmproj_path = lmstudio_mmproj
            downloaded = downloaded and mmproj_path.exists()
        result.append(
            {
                "key": key,
                "model_id": entry.get("model_id", key),
                "size_gb": entry.get("size_gb"),
                "tags": entry.get("tags", []),
                "backend": entry.get("backend", "llama_cpp"),
                "multimodal": bool(entry.get("multimodal", False)),
                "modalities": entry.get("modalities", []),
                "downloaded": downloaded,
                "path": str(resolved_path),
                "mmproj_path": str(mmproj_path) if mmproj_path else None,
            }
        )
    return result


class ServerHandle:
    def __init__(self, server: Any, thread: Any | None = None, manager: Any | None = None):
        self._server = server
        self._thread = thread
        self._manager = manager

    def shutdown(self) -> None:
        self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=10)
        if self._manager is not None:
            self._manager.shutdown()
