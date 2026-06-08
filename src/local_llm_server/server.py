"""
server.py — generic OpenAI-compatible HTTP server built on stdlib ThreadingHTTPServer.

All model-specific logic lives in the registry/config layer; this file has
no knowledge of any particular model name.
"""
from __future__ import annotations

import json
import logging
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("local-llm.server")


# ── JSON helpers ────────────────────────────────────────────────────────────────

def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as exc:
        logger.debug("Client disconnected before response could be sent: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error sending JSON response: %s", exc)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length") or "0")
    if content_length <= 0:
        return {}
    raw_body = handler.rfile.read(content_length).decode("utf-8")
    value = json.loads(raw_body)
    if not isinstance(value, dict):
        raise ValueError("Request body must be a JSON object.")
    return value


# ── Message normalisation ───────────────────────────────────────────────────────

def _normalize_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Accept both OpenAI-style {messages:[…]} and LM-Studio-style {input:…}."""
    raw_messages = payload.get("messages")

    if isinstance(raw_messages, list):
        messages: list[dict[str, str]] = []
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            content = item.get("content")
            if isinstance(content, list):
                parts = [
                    p if isinstance(p, str) else p.get("text", "")
                    for p in content
                    if isinstance(p, (str, dict))
                ]
                content = "\n".join(p for p in parts if p)
            content = str(content or "").strip()
            if role and content:
                messages.append({"role": role, "content": content})
        if messages:
            return messages

    system_prompt = str(payload.get("system_prompt") or "").strip()
    user_input = str(
        payload.get("input") or payload.get("text") or payload.get("prompt") or ""
    ).strip()

    if not user_input:
        raise ValueError("Missing required field: 'messages' or 'input'.")

    msgs: list[dict[str, str]] = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": user_input})
    return msgs


# ── Response helpers ────────────────────────────────────────────────────────────

def _extract_choice_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                text = item if isinstance(item, str) else item.get("text") or item.get("content", "")
                if isinstance(text, str):
                    parts.append(text)
            return "\n".join(parts)
    text = first.get("text")
    return text if isinstance(text, str) else ""


def _strip_thinking(content: str) -> tuple[str, str]:
    """Return (thinking, final_answer) from a content string."""
    if "<think>" in content and "</think>" in content:
        before, rest = content.split("<think>", 1)
        thinking, after = rest.split("</think>", 1)
        return thinking.strip(), (before + after).strip()
    return "", content.strip()


def _usage_stats(response: dict[str, Any], started_at: float, finished_at: float) -> dict[str, Any]:
    usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    elapsed = max(finished_at - started_at, 1e-6)
    return {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "tokens_per_second": completion_tokens / elapsed if completion_tokens else 0.0,
        "time_total_seconds": elapsed,
    }


def _build_response(
    raw: dict[str, Any],
    *,
    model_id: str,
    backend: str,
    started_at: float,
    finished_at: float,
    show_thinking: bool,
) -> dict[str, Any]:
    content = _extract_choice_content(raw)
    thinking, final_answer = _strip_thinking(content)
    exposed = content if show_thinking else final_answer

    payload = dict(raw)
    payload["model"] = model_id
    payload["output"] = exposed
    payload["response"] = exposed
    payload["content"] = exposed
    payload["raw_output"] = content
    payload["thinking"] = thinking
    payload["final_answer"] = final_answer
    payload["backend"] = backend
    payload["stats"] = _usage_stats(raw, started_at, finished_at)
    return payload


# ── Server ──────────────────────────────────────────────────────────────────────

class LocalLLMServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        llm: Any,
        cfg: dict[str, Any],
    ) -> None:
        super().__init__(server_address, handler_class)
        self.llm = llm
        self.cfg = cfg
        self.generation_lock = threading.Lock()
        self.current_status: dict[str, Any] = {
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

    def handle_error(self, request: Any, client_address: Any) -> None:
        exc_type = sys.exc_info()[0]
        if exc_type and issubclass(exc_type, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            logger.debug("Client %s disconnected (%s)", client_address, exc_type.__name__)
            return
        super().handle_error(request, client_address)


class LLMHandler(BaseHTTPRequestHandler):
    server_version = "LocalLLMServer/0.1"

    @property
    def app(self) -> LocalLLMServer:
        return self.server  # type: ignore[return-value]

    def handle_one_request(self) -> None:
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        try:
            super().log_request(code, size)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - " + fmt, self.address_string(), *args)

    # ── GET ──────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        cfg = self.app.cfg

        if path in {"/", "/health"}:
            _json_response(self, 200, {
                "ok": True,
                "server": "local-llm-server",
                "backend": getattr(self.app.llm, "backend", cfg.get("backend", "unknown")),
                "model": cfg["model_id"],
                "model_path": cfg["model_path"],
                "endpoints": [
                    "GET /v1/models",
                    "POST /v1/chat/completions",
                    "GET /status",
                ],
            })
            return

        if path in {"/v1/models", "/api/v1/models"}:
            _json_response(self, 200, {
                "object": "list",
                "data": [{
                    "id": cfg["model_id"],
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "local",
                    "path": cfg["model_path"],
                }],
            })
            return

        if path in {"/status", "/api/v1/status"}:
            status = dict(self.app.current_status)
            if status["active"] and status["phase"] == "generating" and status["tokens_generated"] > 0:
                elapsed = time.perf_counter() - status["started_at"]
                if elapsed > 0:
                    status["tokens_per_second"] = status["tokens_generated"] / elapsed
            _json_response(self, 200, status)
            return

        _json_response(self, 404, {"error": f"Unknown route: {self.path}"})

    # ── POST ─────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/")

        if path in {"/v1/chat/completions", "/api/v1/chat"}:
            self._handle_chat()
            return

        # LM Studio compat: /api/v1/models/load — model is already loaded
        if path == "/api/v1/models/load":
            _json_response(self, 200, {
                "ok": True,
                "model": self.app.cfg["model_id"],
                "already_loaded": True,
            })
            return

        _json_response(self, 404, {"error": f"Unknown route: {self.path}"})

    # ── Inference ─────────────────────────────────────────────────────────────

    def _handle_chat(self) -> None:
        cfg = self.app.cfg
        started_at = time.perf_counter()

        try:
            request_payload = _read_json(self)
            messages = _normalize_messages(request_payload)

            max_tokens = request_payload.get("max_tokens") or request_payload.get("max_output_tokens")

            kwargs: dict[str, Any] = {
                "messages": messages,
                "temperature": float(request_payload.get("temperature", cfg.get("default_temperature", 0.0))),
                "top_p": float(request_payload.get("top_p", 1.0)),
                "top_k": int(request_payload.get("top_k", 40)),
                "min_p": float(request_payload.get("min_p", 0.05)),
                "repeat_penalty": float(request_payload.get("repeat_penalty", 1.0)),
                "presence_penalty": float(request_payload.get("presence_penalty", 0.0)),
                "frequency_penalty": float(request_payload.get("frequency_penalty", 0.0)),
                "stream": True,
                "model": str(request_payload.get("model") or cfg["model_id"]),
            }

            if max_tokens is not None:
                kwargs["max_tokens"] = int(max_tokens)
            if request_payload.get("seed") is not None:
                kwargs["seed"] = int(request_payload["seed"])
            if request_payload.get("stop") is not None:
                kwargs["stop"] = request_payload["stop"]

            if isinstance(request_payload.get("response_format"), dict):
                kwargs["response_format"] = request_payload["response_format"]
            elif cfg["force_json"]:
                kwargs["response_format"] = {"type": "json_object"}

            with self.app.generation_lock:
                self.app.current_status.update({
                    "active": True,
                    "phase": "prompt_eval",
                    "tokens_generated": 0,
                    "max_tokens": int(max_tokens) if max_tokens else 0,
                    "started_at": time.perf_counter(),
                })

                stream = self.app.llm.create_chat_completion(**kwargs)

                full_content = ""
                raw_response = None
                is_thinking = False

                print(f"\n\033[94m[{time.strftime('%H:%M:%S')}] LLM inference started…\033[0m", flush=True)

                for chunk in stream:
                    if self.app.current_status["phase"] == "prompt_eval":
                        self.app.current_status["phase"] = "generating"
                        self.app.current_status["started_at"] = time.perf_counter()
                        print("\033[90mPrompt evaluated. Generating:\033[0m\n", end="", flush=True)

                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        if "<think>" in token:
                            is_thinking = True
                            print("\n\033[93m[THINKING]\033[0m ", end="", flush=True)
                        print(f"\033[90m{token}\033[0m" if is_thinking else token, end="", flush=True)
                        if "</think>" in token:
                            is_thinking = False
                            print("\n\033[92m[RESPONSE]\033[0m ", end="", flush=True)

                        full_content += token
                        self.app.current_status["tokens_generated"] += 1
                        self.app.current_status["last_token_at"] = time.perf_counter()
                        self.app.current_status["last_content"] = full_content[-100:]

                    if raw_response is None:
                        raw_response = chunk

                print("\n\033[94m[Inference complete]\033[0m\n", flush=True)

                if raw_response:
                    raw_response["choices"][0]["message"] = {"role": "assistant", "content": full_content}
                    raw_response["usage"] = {
                        "prompt_tokens": 0,
                        "completion_tokens": self.app.current_status["tokens_generated"],
                        "total_tokens": self.app.current_status["tokens_generated"],
                    }

            finished_at = time.perf_counter()

        except json.JSONDecodeError as exc:
            self.app.current_status["active"] = False
            _json_response(self, 400, {"error": f"Invalid JSON: {exc}"})
            return
        except ValueError as exc:
            self.app.current_status["active"] = False
            _json_response(self, 400, {"error": str(exc)})
            return
        except Exception as exc:
            self.app.current_status["active"] = False
            import traceback
            logger.error("Inference error:\n%s", traceback.format_exc())
            _json_response(self, 500, {"error": f"Inference failed: {exc}"})
            return
        finally:
            self.app.current_status["active"] = False

        if not isinstance(raw_response, dict):
            _json_response(self, 500, {"error": "Inference engine returned a non-dict response."})
            return

        response = _build_response(
            raw_response,
            model_id=cfg["model_id"],
            backend=getattr(self.app.llm, "backend", cfg.get("backend", "unknown")),
            started_at=started_at,
            finished_at=finished_at,
            show_thinking=cfg["show_thinking"],
        )
        _json_response(self, 200, response)


# ── Public entry point ──────────────────────────────────────────────────────────

def run_server(cfg: dict[str, Any], llm: Any) -> None:
    """Start the server and block until SIGINT/SIGTERM."""
    import signal

    try:
        server = LocalLLMServer(
            (cfg["host"], cfg["port"]),
            LLMHandler,
            llm=llm,
            cfg=cfg,
        )
    except OSError as exc:
        raise SystemExit(
            f"Cannot bind http://{cfg['host']}:{cfg['port']}: {exc}. "
            "Choose a different port with --port."
        ) from exc

    def _shutdown(signum: int, _frame: Any) -> None:
        logger.info("Signal %d received — shutting down.", signum)
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "local-llm-server listening on http://%s:%d/v1/chat/completions  (model: %s)",
        cfg["host"],
        cfg["port"],
        cfg["model_id"],
    )

    try:
        server.serve_forever()
    finally:
        server.server_close()
