"""
engine.py — load either llama-cpp-python or mlx-lm depending on configuration.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterator

from .downloader import ensure_model

logger = logging.getLogger("local-llm.engine")


class LlamaCppEngine:
    backend = "llama-cpp-python"

    def __init__(self, cfg: dict[str, Any]) -> None:
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

        logger.info("Loading GGUF model: %s", model_path)
        logger.info(
            "Model configuration: %s",
            json.dumps({k: v for k, v in kwargs.items() if k != "model_path"}, indent=2),
        )

        self.llm = Llama(**kwargs)

    def create_chat_completion(self, **kwargs: Any) -> Any:
        return self.llm.create_chat_completion(**kwargs)


class MLXEngine:
    backend = "mlx-lm"

    def __init__(self, cfg: dict[str, Any]) -> None:
        try:
            from mlx_lm import load
        except ModuleNotFoundError as exc:
            raise SystemExit(
                "Missing dependency: mlx-lm. "
                'Install it with: pip install "local-llm-server[mlx]"'
            ) from exc

        self.model_ref = str(cfg["model_path"])
        self.cfg = cfg

        tokenizer_config = cfg.get("tokenizer_config") or {"trust_remote_code": True}

        logger.info("Loading MLX model: %s", self.model_ref)
        self.model, self.tokenizer = load(
            self.model_ref,
            tokenizer_config=tokenizer_config,
        )
        logger.info("MLX model loaded.")

    def create_chat_completion(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_logits_processors, make_sampler

        messages = kwargs["messages"]
        max_tokens = int(kwargs.get("max_tokens") or 512)

        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
        )

        sampler = make_sampler(
            temp=float(kwargs.get("temperature", 0.0)),
            top_p=float(kwargs.get("top_p", 1.0)),
            min_p=float(kwargs.get("min_p", 0.0)),
            top_k=int(kwargs.get("top_k", 0)),
        )

        logits_processors = make_logits_processors(
            repetition_penalty=kwargs.get("repeat_penalty"),
            presence_penalty=kwargs.get("presence_penalty"),
            frequency_penalty=kwargs.get("frequency_penalty"),
        )

        model_name = str(kwargs.get("model") or self.model_ref)

        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            sampler=sampler,
            logits_processors=logits_processors,
            max_kv_size=self.cfg.get("max_kv_size"),
        ):
            text = response.text or ""
            if not text:
                continue

            yield {
                "id": "chatcmpl-local-mlx",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": text},
                        "finish_reason": None,
                    }
                ],
            }


def load_llm(cfg: dict[str, Any]) -> Any:
    backend = cfg.get("backend", "llama_cpp")

    if backend in {"llama_cpp", "gguf"}:
        return LlamaCppEngine(cfg)

    if backend == "mlx":
        return MLXEngine(cfg)

    raise ValueError(f"Unsupported backend: {backend}")
