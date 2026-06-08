"""local_llm_server — public API."""
from __future__ import annotations

from .server import run_server

__all__ = ["run_server"]


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
    import threading
    from .config import build_config
    from .engine import load_llm
    from .server import LocalLLMServer, LLMHandler

    cfg = build_config(
        model=model,
        model_path=model_path,
        host=host,
        port=port,
        no_download=no_download,
        **kwargs,
    )
    llm = load_llm(cfg)
    server = LocalLLMServer(
        (cfg["host"], cfg["port"]),
        LLMHandler,
        llm=llm,
        cfg=cfg,
    )

    if background:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return _ServerHandle(server)

    import signal as _signal

    def _shutdown(signum, _frame):
        threading.Thread(target=server.shutdown, daemon=True).start()

    _signal.signal(_signal.SIGINT, _shutdown)
    _signal.signal(_signal.SIGTERM, _shutdown)
    try:
        server.serve_forever()
    finally:
        server.server_close()
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
        result.append(
            {
                "key": key,
                "model_id": entry.get("model_id", key),
                "size_gb": entry.get("size_gb"),
                "tags": entry.get("tags", []),
                "downloaded": path.exists(),
                "path": str(path),
            }
        )
    return result


class _ServerHandle:
    def __init__(self, server):
        self._server = server

    def shutdown(self) -> None:
        self._server.shutdown()
        self._server.server_close()
