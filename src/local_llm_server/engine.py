"""
engine.py — load either llama-cpp-python or mlx-lm depending on configuration.
"""
from __future__ import annotations

import json
import logging
import atexit
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
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
        kwargs.pop("enable_thinking", None)
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

        enable_thinking = kwargs.pop("enable_thinking", None)
        template_kwargs = {}
        if enable_thinking is not None:
            template_kwargs["enable_thinking"] = enable_thinking
            template_kwargs["thinking"] = enable_thinking

        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            **template_kwargs,
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


class LlamaServerEngine:
    """
    Engine backed by an external llama-server subprocess.

    This is intended for llama.cpp features not exposed reliably through
    llama-cpp-python, such as multimodal projectors passed with --mmproj.
    """

    backend = "llama_server"

    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.model_path = Path(cfg["model_path"]).expanduser()
        self.mmproj_path = Path(cfg["mmproj_path"]).expanduser() if cfg.get("mmproj_path") else None
        self.port = int(cfg.get("llama_server_port") or 8091)
        self.host = "127.0.0.1"
        self.base_url = f"http://{self.host}:{self.port}"
        self.process: subprocess.Popen[str] | None = None

        ensure_model(
            url=cfg.get("download_url", ""),
            dest=self.model_path,
            no_download=cfg.get("no_download", False),
        )
        if self.mmproj_path and not self.mmproj_path.exists():
            raise FileNotFoundError(f"Multimodal projector not found: {self.mmproj_path}")

        self.binary = self._resolve_binary(cfg)
        self._start()
        atexit.register(self.shutdown)

    @staticmethod
    def _resolve_binary(cfg: dict[str, Any]) -> Path:
        candidates: list[Path] = []
        explicit = cfg.get("llama_server_bin") or os.getenv("LOCAL_LLM_SERVER_BIN")
        if explicit:
            candidates.append(Path(str(explicit)).expanduser())

        lmstudio_backends = Path.home() / ".lmstudio" / "extensions" / "backends"
        candidates.extend(
            sorted(
                lmstudio_backends.glob("llama.cpp-*/llama-server"),
                key=lambda p: p.parent.name,
                reverse=True,
            )
        )

        which = shutil.which("llama-server")
        if which:
            candidates.append(Path(which))

        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate

        searched = ", ".join(str(p) for p in candidates) or "no candidates"
        raise FileNotFoundError(
            "llama-server binary not found. Set LOCAL_LLM_SERVER_BIN or "
            f"llama_server_bin to an executable path. Searched: {searched}"
        )

    def _start(self) -> None:
        cmd = [
            str(self.binary),
            "-m",
            str(self.model_path),
            "--port",
            str(self.port),
            "--host",
            self.host,
            "-c",
            str(self.cfg.get("ctx_size", 4096)),
        ]
        if self.mmproj_path:
            cmd.extend(["--mmproj", str(self.mmproj_path)])

        logger.info("Starting llama-server: %s", " ".join(cmd))
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._wait_until_ready(timeout=float(self.cfg.get("startup_timeout") or 60))

    def _wait_until_ready(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        last_error = ""
        while time.monotonic() < deadline:
            if self.process and self.process.poll() is not None:
                output = ""
                if self.process.stdout:
                    output = self.process.stdout.read()[-4000:]
                raise RuntimeError(f"llama-server exited during startup. {output}")
            try:
                with urllib.request.urlopen(f"{self.base_url}/health", timeout=2) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status == 200 and (not body or '"ok"' in body or '"status"' in body):
                        logger.info("llama-server ready on %s", self.base_url)
                        return
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = str(exc)
            time.sleep(1)
        self.shutdown()
        raise TimeoutError(f"llama-server did not become ready within {timeout:.0f}s. Last error: {last_error}")

    def create_chat_completion(self, **kwargs: Any) -> Any:
        enable_thinking = kwargs.pop("enable_thinking", None)
        if enable_thinking is not None and "chat_template_kwargs" not in kwargs:
            # For modern llama-server templates that support enable_thinking variable
            kwargs["chat_template_kwargs"] = {"enable_thinking": enable_thinking}

        stream = bool(kwargs.get("stream"))
        payload = json.dumps(kwargs).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        if not stream:
            with urllib.request.urlopen(request, timeout=float(self.cfg.get("timeout") or 1200)) as response:
                return json.loads(response.read().decode("utf-8"))

        def iter_chunks() -> Iterator[dict[str, Any]]:
            with urllib.request.urlopen(request, timeout=float(self.cfg.get("timeout") or 1200)) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    yield json.loads(data)

        return iter_chunks()

    def shutdown(self) -> None:
        process = self.process
        if process is None or process.poll() is not None:
            return
        logger.info("Stopping llama-server on port %s", self.port)
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def load_llm(cfg: dict[str, Any]) -> Any:
    backend = cfg.get("backend", "llama_cpp")

    if backend in {"llama_cpp", "gguf"}:
        return LlamaCppEngine(cfg)

    if backend == "mlx":
        return MLXEngine(cfg)

    if backend == "llama_server":
        return LlamaServerEngine(cfg)

    raise ValueError(f"Unsupported backend: {backend}")
