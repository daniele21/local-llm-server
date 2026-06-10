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
        choices=["llama_cpp", "mlx"],
        default=None,
        help="Inference backend: llama_cpp for GGUF, mlx for MLX models.",
    )
    p_serve.add_argument(
        "--model",
        default=None,
        help="Registry key (e.g. qwen3-8b). Default: registry default_model.",
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
    p_serve.add_argument("--n-gpu-layers", type=int, default=None, dest="n_gpu_layers")
    p_serve.add_argument("--n-threads", type=int, default=None, dest="n_threads")
    p_serve.add_argument("--chat-format", default=None, dest="chat_format")
    p_serve.add_argument("--force-json", action=argparse.BooleanOptionalAction, default=None)
    p_serve.add_argument("--show-thinking", action=argparse.BooleanOptionalAction, default=None, dest="show_thinking")
    p_serve.add_argument("--enable-thinking", action=argparse.BooleanOptionalAction, default=None, dest="enable_thinking")
    p_serve.add_argument("--no-download", action="store_true", default=False, dest="no_download",
                         help="Fail if the model is not already downloaded.")
    p_serve.add_argument("--verbose", action="store_true", default=False)

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

    # Collect only explicitly set flags (skip None so config resolution works)
    explicit: dict = {}
    for key in ("backend", "host", "port", "ctx_size", "n_gpu_layers", "n_threads",
                "chat_format", "force_json", "show_thinking", "enable_thinking",
                "no_download", "verbose"):
        val = getattr(args, key, None)
        if val is not None:
            explicit[key] = val

    cfg = build_config(
        model=args.model,
        model_path=args.model_path,
        **explicit,
    )

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    llm = load_llm(cfg)
    run_server(cfg, llm)


def _cmd_models() -> None:
    from .registry import load_registry

    registry = load_registry()
    models_dir = registry["models_dir"]
    default = registry["default_model"]
    models = registry["models"]

    if not models:
        print("No models found in registry.")
        return

    print(f"\nAvailable models  (dir: {models_dir})\n")
    col_key = max(len(k) for k in models) + 2
    col_id = max(len(v.get("model_id", k)) for k, v in models.items()) + 2

    for key, entry in models.items():
        model_id = entry.get("model_id", key)
        size = f"{entry['size_gb']:.1f} GB" if entry.get("size_gb") else "? GB"
        tags = ", ".join(entry.get("tags") or [])
        path = models_dir / entry["filename"]
        status = "\033[92m✅ downloaded\033[0m" if path.exists() else "\033[90m❌ not downloaded\033[0m"
        marker = " (default)" if key == default else ""
        print(f"  {key:<{col_key}} {model_id:<{col_id}} {size:<8}  [{tags}]  {status}{marker}")

    print()


def _cmd_download(model: str) -> None:
    from .registry import load_registry
    from .downloader import download_model

    registry = load_registry()
    entry = registry["models"].get(model)
    if entry is None:
        print(f"Error: model '{model}' not found in registry.", file=sys.stderr)
        print("Run 'local-llm models' to see available models.", file=sys.stderr)
        sys.exit(1)

    url = entry.get("url", "")
    if not url:
        print(f"Error: no download URL configured for model '{model}'.", file=sys.stderr)
        sys.exit(1)

    dest = registry["models_dir"] / entry["filename"]
    if dest.exists():
        print(f"Model already downloaded: {dest}")
        return

    size_str = f" ({entry['size_gb']:.1f} GB)" if entry.get("size_gb") else ""
    print(f"Downloading {model}{size_str}…")
    download_model(url=url, dest=dest)
    print(f"Done: {dest}")
