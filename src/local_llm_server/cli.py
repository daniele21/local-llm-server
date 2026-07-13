"""
cli.py — entry point for the `local-llm` command.

Subcommands:
  local-llm serve    — start the HTTP server
  local-llm models   — list available models
  local-llm download — download a model without starting the server
"""
from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="local-llm",
        description="Self-contained local LLM server with OpenAI-compatible API.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── serve ─────────────────────────────────────────────────────────────────
    p_serve = sub.add_parser("serve", help="Start the LLM server.")
    p_serve.add_argument(
        "--backend",
        choices=["llama_cpp", "mlx", "llama_server", "mlx_vlm_server"],
        default=None,
        help="Inference backend: llama_cpp for GGUF, mlx for text MLX, llama_server for GGUF multimodal, mlx_vlm_server for MLX vision.",
    )
    p_serve.add_argument(
        "--model",
        default=None,
        help="Registry key (e.g. qwen3-8b). Default: registry default_model.",
    )
    p_serve.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Registry keys to keep resident simultaneously.",
    )
    p_serve.add_argument(
        "--default-model",
        default=None,
        dest="default_model",
        help="Default route when a request omits the model field.",
    )
    p_serve.add_argument(
        "--model-path",
        default=None,
        dest="model_path",
        help="Direct model path/ref. For llama_cpp: .gguf file. For mlx: local MLX dir or HF repo.",
    )
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", type=int, default=None)
    p_serve.add_argument("--ctx-size", type=int, default=None, dest="ctx_size")
    p_serve.add_argument(
        "--max-kv-size", type=int, default=None, dest="max_kv_size",
        help="Maximum MLX KV-cache size in tokens.",
    )
    p_serve.add_argument("--n-gpu-layers", type=int, default=None, dest="n_gpu_layers")
    p_serve.add_argument("--n-threads", type=int, default=None, dest="n_threads")
    p_serve.add_argument("--llama-server-port", type=int, default=None, dest="llama_server_port")
    p_serve.add_argument("--llama-server-bin", default=None, dest="llama_server_bin")
    p_serve.add_argument("--mlx-vlm-server-port", type=int, default=None, dest="mlx_vlm_server_port")
    p_serve.add_argument("--mmproj-path", default=None, dest="mmproj_path")
    p_serve.add_argument("--startup-timeout", type=int, default=None, dest="startup_timeout")
    p_serve.add_argument("--max-concurrent-requests", type=int, default=None, dest="max_concurrent_requests")
    p_serve.add_argument("--chat-format", default=None, dest="chat_format")
    p_serve.add_argument("--force-json", action=argparse.BooleanOptionalAction, default=None)
    p_serve.add_argument("--show-thinking", action=argparse.BooleanOptionalAction, default=None, dest="show_thinking")
    p_serve.add_argument("--enable-thinking", action=argparse.BooleanOptionalAction, default=None, dest="enable_thinking")
    p_serve.add_argument("--no-download", action="store_true", default=False, dest="no_download",
                         help="Fail if the model is not already downloaded.")
    p_serve.add_argument("--verbose", action="store_true", default=False)
    p_serve.add_argument(
        "--enable-admin-api",
        action="store_true",
        default=False,
        help="Enable model management, registry, and log-stream endpoints.",
    )
    p_serve.add_argument(
        "--cors-origin",
        action="append",
        default=[],
        help="Allowed browser origin; repeat for multiple origins. CORS is disabled by default.",
    )

    # ── models ────────────────────────────────────────────────────────────────
    sub.add_parser("models", help="List available models from the registry.")

    # ── download ──────────────────────────────────────────────────────────────
    p_download = sub.add_parser("download", help="Download a model without starting the server.")
    p_download.add_argument("model", help="Registry key (e.g. qwen3-8b).")

    args = parser.parse_args()

    if args.command == "serve":
        _cmd_serve(args)
    elif args.command == "models":
        _cmd_models()
    elif args.command == "download":
        _cmd_download(args.model)


def _cmd_serve(args: argparse.Namespace) -> None:
    from .config import build_config
    from .engine import load_llm
    from .server import run_server
    from .registry import load_registry
    from .runtime import ModelRuntimeManager

    # Collect only explicitly set flags (skip None so config resolution works)
    explicit: dict = {}
    for key in ("backend", "host", "port", "ctx_size", "max_kv_size", "n_gpu_layers", "n_threads",
                "llama_server_port", "llama_server_bin", "mlx_vlm_server_port", "mmproj_path", "startup_timeout",
                "max_concurrent_requests",
                "chat_format", "force_json", "show_thinking", "enable_thinking",
                "no_download", "verbose"):
        val = getattr(args, key, None)
        if val is not None:
            explicit[key] = val

    registry = load_registry()
    startup_models = list(args.models or registry.get("startup_models") or [])
    if startup_models:
        default_model = args.default_model or args.model or startup_models[0]
        if default_model not in startup_models:
            startup_models.insert(0, default_model)
        manager = ModelRuntimeManager(default_model=default_model)
        try:
            for model_key in startup_models:
                per_model_explicit = dict(explicit)
                if model_key != default_model:
                    per_model_explicit.pop("llama_server_port", None)
                    per_model_explicit.pop("mlx_vlm_server_port", None)
                manager.load(model_key, **per_model_explicit)
        except Exception:
            manager.shutdown()
            raise
        default_runtime = manager.resolve()
        cfg = default_runtime.cfg
        llm = default_runtime.engine
    else:
        cfg = build_config(
            model=args.model,
            model_path=args.model_path,
            **explicit,
        )
        llm = load_llm(cfg)
        manager = None

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run_server(
        cfg,
        llm,
        manager=manager,
        enable_admin_api=args.enable_admin_api,
        cors_origins=args.cors_origin,
    )


def _cmd_models() -> None:
    from . import list_models
    from .registry import load_registry

    registry = load_registry()
    models_dir = registry["models_dir"]
    default = registry["default_model"]
    models = list_models()

    if not models:
        print("No models found in registry.")
        return

    print(f"\nAvailable models  (dir: {models_dir})\n")
    col_key = max(len(entry["key"]) for entry in models) + 2
    col_id = max(len(entry["model_id"]) for entry in models) + 2

    for entry in models:
        key = entry["key"]
        model_id = entry["model_id"]
        size = f"{entry['size_gb']:.1f} GB" if entry.get("size_gb") else "? GB"
        tags = ", ".join(entry.get("tags") or [])
        model_ready = bool(entry["downloaded"])
        status = "\033[92m✅ downloaded\033[0m" if model_ready else "\033[90m❌ not downloaded\033[0m"
        marker = " (default)" if key == default else ""
        backend = entry.get("backend", "llama_cpp")
        print(f"  {key:<{col_key}} {model_id:<{col_id}} {size:<8}  {backend:<13} [{tags}]  {status}{marker}")

    print()


def _cmd_download(model: str) -> None:
    from . import download_model

    try:
        download_model(model)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Model '{model}' is available locally.")
