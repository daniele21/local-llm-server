"""
server.py — OpenAI-compatible HTTP server built on FastAPI.
Provides automatically generated interactive OpenAPI documentation at /docs.
"""
from __future__ import annotations

import os
import subprocess
import shlex
import asyncio
import json
import logging
import sys
import threading
import time
import queue
import collections
from pathlib import Path
from typing import Any, List, Dict, Optional, Union

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger("local-llm.server")

# ── Log capturing infrastructure ───────────────────────────────────────────────

class LogStreamBuffer:
    def __init__(self, limit: int = 2000) -> None:
        self.buffer: collections.deque[str] = collections.deque(maxlen=limit)
        self.listeners: list[queue.Queue[str]] = []
        self.lock = threading.Lock()

    def append(self, text: str) -> None:
        if not text:
            return
        with self.lock:
            self.buffer.append(text)
            self.listeners = [listener for listener in self.listeners if not getattr(listener, "closed", False)]
            for listener in self.listeners:
                try:
                    listener.put_nowait(text)
                except queue.Full:
                    pass

    def add_listener(self) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=1000)
        q.closed = False  # type: ignore[attr-defined]
        with self.lock:
            for item in self.buffer:
                q.put_nowait(item)
            self.listeners.append(q)
        return q


log_buffer = LogStreamBuffer(limit=2000)


class DualWriter:
    def __init__(self, original: Any, buffer: LogStreamBuffer) -> None:
        self.original = original
        self.buffer = buffer
        self._accumulator = ""

    def write(self, text: str) -> None:
        self.original.write(text)
        self.original.flush()
        
        self._accumulator += text
        while "\n" in self._accumulator:
            line, self._accumulator = self._accumulator.split("\n", 1)
            line = line.rstrip("\r")
            if line.strip():
                self.buffer.append(line)

    def flush(self) -> None:
        self.original.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.original, name)


# Redirect python's print outputs
sys.stdout = DualWriter(sys.stdout, log_buffer)
sys.stderr = DualWriter(sys.stderr, log_buffer)


class LogBufferHandler(logging.Handler):
    def __init__(self, buffer: LogStreamBuffer) -> None:
        super().__init__()
        self.buffer = buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.buffer.append(msg)
        except Exception:
            self.handleError(record)


# Add logging handler to the root logger to capture all python logs
log_handler = LogBufferHandler(log_buffer)
log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s", datefmt="%H:%M:%S")
log_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(log_handler)


# ── Pydantic Request Models for Swagger ──────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message author (e.g. system, user, assistant).")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The content of the message.")

class ChatCompletionRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = Field(None, description="OpenAI-compatible list of messages.")
    system_prompt: Optional[str] = Field(None, description="Legacy LM Studio system prompt.")
    input: Optional[str] = Field(None, description="Legacy LM Studio input prompt.")
    text: Optional[str] = Field(None, description="Legacy LM Studio input prompt alias.")
    prompt: Optional[str] = Field(None, description="Legacy LM Studio input prompt alias.")
    model: Optional[str] = Field(None, description="ID of the model to use.")
    temperature: Optional[float] = Field(None, description="Sampling temperature.")
    top_p: Optional[float] = Field(None, description="Nucleus sampling threshold.")
    top_k: Optional[int] = Field(None, description="Top-k sampling threshold.")
    min_p: Optional[float] = Field(None, description="Min-p sampling threshold.")
    repeat_penalty: Optional[float] = Field(None, description="Penalty for repeating tokens.")
    presence_penalty: Optional[float] = Field(None, description="OpenAI-compatible presence penalty.")
    frequency_penalty: Optional[float] = Field(None, description="OpenAI-compatible frequency penalty.")
    stream: Optional[bool] = Field(False, description="Enable streaming response.")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate.")
    max_output_tokens: Optional[int] = Field(None, description="Maximum tokens to generate (alias).")
    seed: Optional[int] = Field(None, description="Random seed for deterministic output.")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequence(s).")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Format specifications (e.g. {'type': 'json_object'}).")
    enable_thinking: Optional[bool] = Field(None, description="Request-level override to enable reasoning/thinking where supported.")
    show_thinking: Optional[bool] = Field(None, description="Request-level override to show or hide <think> blocks in output.")
    enable_reasoning: Optional[bool] = Field(None, description="Alias for enable_thinking.")
    show_reasoning: Optional[bool] = Field(None, description="Alias for show_thinking.")


class TerminalCommandRequest(BaseModel):
    command: str = Field(..., description="The terminal command to execute.")


class ModelActivateRequest(BaseModel):
    model: str = Field(..., description="Registry key of the model to activate.")
    backend: Optional[str] = Field(None, description="Inference backend override (llama_cpp, mlx, or llama_server).")
    ctx_size: Optional[int] = Field(None, description="Context size override.")
    n_gpu_layers: Optional[int] = Field(None, description="Number of GPU layers override.")
    n_threads: Optional[int] = Field(None, description="Number of CPU threads override.")
    n_batch: Optional[int] = Field(None, description="Batch size override.")
    n_ubatch: Optional[int] = Field(None, description="Micro-batch size override.")
    offload_kqv: Optional[bool] = Field(None, description="Offload KQV to GPU.")
    flash_attn: Optional[bool] = Field(None, description="Enable Flash Attention.")
    use_mmap: Optional[bool] = Field(None, description="Use mmap for model loading.")
    timeout: Optional[int] = Field(None, description="Inference timeout in seconds.")
    llama_server_port: Optional[int] = Field(None, description="Internal llama-server subprocess port.")
    llama_server_bin: Optional[str] = Field(None, description="Path to llama-server executable.")
    mmproj_path: Optional[str] = Field(None, description="Path to multimodal projector GGUF.")
    startup_timeout: Optional[int] = Field(None, description="llama-server startup timeout in seconds.")
    enable_thinking: Optional[bool] = Field(None, description="Enable thinking mode globally.")
    show_thinking: Optional[bool] = Field(None, description="Show thinking globally.")
    verbose: Optional[bool] = Field(None, description="Verbose logging.")


# ── Message normalisation ───────────────────────────────────────────────────────

def _normalize_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Accept both OpenAI-style {messages:[…]} and LM-Studio-style {input:…}."""
    raw_messages = payload.get("messages")

    if isinstance(raw_messages, list):
        messages: list[dict[str, Any]] = []
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip()
            content = item.get("content")
            if isinstance(content, list):
                has_non_text_part = any(
                    isinstance(part, dict) and part.get("type") not in {None, "text"}
                    for part in content
                )
                if not has_non_text_part:
                    parts = [
                        p if isinstance(p, str) else p.get("text", "")
                        for p in content
                        if isinstance(p, (str, dict))
                    ]
                    content = "\n".join(p for p in parts if p)
            if isinstance(content, str):
                content = content.strip()
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
    elif "</think>" in content:
        thinking, after = content.split("</think>", 1)
        return thinking.strip(), after.strip()
    elif "<think>" in content:
        before, thinking = content.split("<think>", 1)
        return thinking.strip(), before.strip()
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
    if "choices" in payload and isinstance(payload["choices"], list) and len(payload["choices"]) > 0:
        import copy
        payload["choices"] = copy.deepcopy(payload["choices"])
        choice = payload["choices"][0]
        if "message" in choice and isinstance(choice["message"], dict):
            choice["message"]["content"] = exposed

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


# ── FastAPI App Creation ────────────────────────────────────────────────────────

app = FastAPI(
    title="Local LLM Server API",
    description="OpenAI-compatible API serving local LLMs (Llama-cpp, MLX, llama-server multimodal).",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
def on_shutdown():
    """Handle server shutdown events."""
    app.state.shutdown = True
    llm = getattr(app.state, "llm", None)
    if llm is not None and hasattr(llm, "shutdown"):
        llm.shutdown()


@app.get("/health", tags=["System"])
def get_health():
    """Check the health status of the LLM server."""
    cfg = app.state.cfg
    llm = app.state.llm
    return {
        "ok": True,
        "server": "local-llm-server",
        "backend": getattr(llm, "backend", cfg.get("backend", "unknown")),
        "model": cfg["model_id"],
        "model_path": cfg["model_path"],
        "host": cfg.get("host"),
        "port": cfg.get("port"),
        "ctx_size": cfg.get("ctx_size"),
        "n_gpu_layers": cfg.get("n_gpu_layers"),
        "n_threads": cfg.get("n_threads"),
        "n_batch": cfg.get("n_batch"),
        "n_ubatch": cfg.get("n_ubatch"),
        "offload_kqv": cfg.get("offload_kqv"),
        "flash_attn": cfg.get("flash_attn"),
        "use_mmap": cfg.get("use_mmap"),
        "timeout": cfg.get("timeout"),
        "enable_thinking": cfg.get("enable_thinking"),
        "show_thinking": cfg.get("show_thinking"),
        "verbose": cfg.get("verbose"),
        "multimodal": cfg.get("multimodal"),
        "modalities": cfg.get("modalities"),
        "mmproj_path": cfg.get("mmproj_path"),
        "llama_server_port": cfg.get("llama_server_port"),
        "model_key": cfg.get("model"),
        "endpoints": [
            "GET /health",
            "GET /v1/models",
            "POST /v1/chat/completions",
            "GET /status",
            "GET /api/v1/logs/stream",
            "GET /api/v1/models/registry",
        ],
    }


@app.get("/v1/models", tags=["Models"])
@app.get("/api/v1/models", tags=["Models"])
def get_models():
    """List loaded models."""
    cfg = app.state.cfg
    return {
        "object": "list",
        "data": [{
            "id": cfg["model_id"],
            "object": "model",
            "created": int(time.time()),
            "owned_by": "local",
            "path": cfg["model_path"],
        }],
    }


@app.get("/status", tags=["System"])
@app.get("/api/v1/status", tags=["System"])
def get_status():
    """Retrieve real-time inference status and speed statistics."""
    status_info = dict(app.state.current_status)
    if status_info["active"] and status_info["phase"] == "generating" and status_info["tokens_generated"] > 0:
        elapsed = time.perf_counter() - status_info["started_at"]
        if elapsed > 0:
            status_info["tokens_per_second"] = status_info["tokens_generated"] / elapsed
    return status_info


@app.get("/api/v1/models/registry", tags=["Models"])
def get_models_registry():
    """List all configured models in local-llm-server registry."""
    try:
        from local_llm_server import list_models
        models = list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {e}"
        )


@app.get("/api/v1/logs/stream", tags=["System"])
def stream_logs(request: Request):
    """SSE endpoint streaming live console logs of the server process."""
    async def log_generator():
        q = log_buffer.add_listener()
        ping_counter = 0
        try:
            while not getattr(app.state, "shutdown", False):
                if await request.is_disconnected():
                    break
                try:
                    msg = q.get_nowait()
                    lines = msg.splitlines()
                    for line in lines:
                        yield f"data: {line}\n\n"
                except queue.Empty:
                    ping_counter += 1
                    if ping_counter >= 25:  # Every 5 seconds (25 * 0.2s)
                        yield ": ping\n\n"
                        ping_counter = 0
                    await asyncio.sleep(0.2)
        except Exception as exc:
            logger.debug("SSE log stream client disconnected: %s", exc)
        finally:
            q.closed = True  # type: ignore[attr-defined]

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/example", response_class=HTMLResponse, tags=["Documentation"])
def get_usage_examples():
    """Retrieve a interactive HTML page showing how to query the local LLM server."""
    cfg = app.state.cfg
    model_id = cfg["model_id"]
    port = cfg["port"]
    host = cfg["host"]
    
    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local LLM Server - API Examples</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --accent: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --card-bg: rgba(30, 41, 59, 0.4);
            --card-border: rgba(255, 255, 255, 0.06);
            --code-bg: #090d16;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2rem 1rem;
            overflow-x: hidden;
        }}

        .container {{
            width: 100%;
            max-width: 900px;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}

        header {{
            text-align: center;
            margin-bottom: 1rem;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #a5b4fc, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        /* Metadata Card */
        .meta-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            display: flex;
            flex-wrap: wrap;
            gap: 1.5rem;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .meta-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            font-weight: 600;
        }}

        .meta-value {{
            font-family: 'Fira Code', monospace;
            font-size: 0.95rem;
            color: #e2e8f0;
            background: rgba(0, 0, 0, 0.25);
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }}

        .meta-value.accent {{
            color: #818cf8;
            font-weight: 500;
        }}

        /* Navigation Links */
        .nav-links {{
            display: flex;
            gap: 1rem;
        }}

        .btn-nav {{
            background: rgba(255, 255, 255, 0.05);
            color: #f1f5f9;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.2s ease;
        }}

        .btn-nav:hover {{
            background: var(--primary);
            border-color: var(--primary);
            box-shadow: 0 0 15px var(--primary-glow);
            transform: translateY(-1px);
        }}

        /* Tabs Interface */
        .tabs-container {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            overflow: hidden;
            backdrop-filter: blur(12px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }}

        .tabs-header {{
            display: flex;
            background: rgba(15, 23, 42, 0.6);
            border-bottom: 1px solid var(--card-border);
            overflow-x: auto;
        }}

        .tab-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            padding: 1.25rem 1.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            white-space: nowrap;
        }}

        .tab-btn:hover {{
            color: var(--text-main);
        }}

        .tab-btn.active {{
            color: var(--primary);
        }}

        .tab-btn.active::after {{
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--primary);
            box-shadow: 0 0 8px var(--primary);
        }}

        .tabs-content {{
            padding: 2rem;
        }}

        .tab-pane {{
            display: none;
            flex-direction: column;
            gap: 1.25rem;
            animation: fadeIn 0.35s ease forwards;
        }}

        .tab-pane.active {{
            display: flex;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .pane-desc {{
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.5;
        }}

        /* Code Block container */
        .code-container {{
            position: relative;
            background: var(--code-bg);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
        }}

        pre {{
            padding: 1.25rem;
            overflow-x: auto;
            margin: 0;
        }}

        code {{
            font-family: 'Fira Code', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            color: #cbd5e1;
        }}

        .btn-copy {{
            position: absolute;
            top: 0.75rem;
            right: 0.75rem;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            color: var(--text-muted);
            cursor: pointer;
            padding: 0.4rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            transition: all 0.2s ease;
        }}

        .btn-copy:hover {{
            background: rgba(255, 255, 255, 0.12);
            color: var(--text-main);
            border-color: rgba(255, 255, 255, 0.2);
        }}

        .btn-copy.copied {{
            background: rgba(16, 185, 129, 0.15);
            border-color: var(--accent);
            color: var(--accent);
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: auto;
            padding-top: 3rem;
            color: rgba(148, 163, 184, 0.4);
            font-size: 0.8rem;
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            .meta-card {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .nav-links {{
                width: 100%;
                justify-content: flex-start;
                margin-top: 0.5rem;
            }}
            .tabs-content {{
                padding: 1.25rem;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>Local LLM Server</h1>
        <p class="subtitle">Esempi pratici e specifiche per l'interrogazione delle API</p>
    </header>

    <!-- Metadata Card -->
    <div class="meta-card">
        <div class="meta-item">
            <span class="meta-label">Modello Attivo</span>
            <span class="meta-value accent">{model_id}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Base URL</span>
            <span class="meta-value">http://{host}:{port}/v1</span>
        </div>
        <div class="nav-links">
            <a href="/" class="btn-nav">Dashboard</a>
            <a href="/docs" class="btn-nav">Swagger Docs</a>
        </div>
    </div>

    <!-- Interactive Tabs -->
    <div class="tabs-container">
        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab(event, 'curl-tab')">cURL Request</button>
            <button class="tab-btn" onclick="switchTab(event, 'openai-tab')">OpenAI Python SDK</button>
            <button class="tab-btn" onclick="switchTab(event, 'requests-tab')">Python Requests</button>
            <button class="tab-btn" onclick="switchTab(event, 'batch-tab')">Test Suite & Batch</button>
        </div>

        <div class="tabs-content">
            <!-- cURL Pane -->
            <div id="curl-tab" class="tab-pane active">
                <p class="pane-desc">Il metodo più semplice per interrogare l'endpoint da terminale usando cURL. Compatibile con lo schema standard di OpenAI.</p>
                <div class="code-container">
                    <button class="btn-copy" onclick="copyCode(this)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        Copy
                    </button>
                    <pre><code id="code-curl">curl http://{host}:{port}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{{
    "model": "{model_id}",
    "messages": [
      {{"role": "system", "content": "Sei un assistente utile e sintetico."}},
      {{"role": "user", "content": "Ciao!"}}
    ],
    "temperature": 0.3
  }}'</code></pre>
                </div>
            </div>

            <!-- OpenAI Python SDK Pane -->
            <div id="openai-tab" class="tab-pane">
                <p class="pane-desc">Utilizza l'SDK ufficiale di OpenAI in Python. È sufficiente cambiare l'indirizzo `base_url` e passare qualsiasi chiave API non vuota.</p>
                <div class="code-container">
                    <button class="btn-copy" onclick="copyCode(this)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        Copy
                    </button>
                    <pre><code id="code-openai">from openai import OpenAI

# Inizializza il client indicando il server locale
client = OpenAI(
    base_url="http://{host}:{port}/v1",
    api_key="local"  # Qualsiasi valore non vuoto è accettato
)

response = client.chat.completions.create(
    model="{model_id}",
    messages=[
        {{"role": "system", "content": "Sei un traduttore dall'italiano all'inglese."}},
        {{"role": "user", "content": "La documentazione rende l'integrazione immediata."}}
    ],
    temperature=0.0
)

print(response.choices[0].message.content)</code></pre>
                </div>
            </div>

            <!-- Python Requests Pane -->
            <div id="requests-tab" class="tab-pane">
                <p class="pane-desc">Per fare chiamate senza installare dipendenze esterne oltre a `requests`.</p>
                <div class="code-container">
                    <button class="btn-copy" onclick="copyCode(this)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        Copy
                    </button>
                    <pre><code id="code-requests">import requests

url = "http://{host}:{port}/v1/chat/completions"
payload = {{
    "model": "{model_id}",
    "messages": [
        {{"role": "system", "content": "Sei un assistente utile e conciso."}},
        {{"role": "user", "content": "Spiega cos'è un LLM in una riga."}}
    ],
    "temperature": 0.5
}}

response = requests.post(url, json=payload)
data = response.json()
print(data["choices"][0]["message"]["content"])</code></pre>
                </div>
            </div>

            <!-- Batch Inference script Pane -->
            <div id="batch-tab" class="tab-pane">
                <p class="pane-desc">Il repository contiene uno script dedicato e modulare per eseguire test di classificazione in batch partendo da liste di parole chiave e configurando risposte strutturate JSON.</p>
                
                <p class="pane-desc"><strong>File dello script:</strong> <code>test_inference.py</code></p>
                
                <div class="code-container">
                    <button class="btn-copy" onclick="copyCode(this)">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                        Copy
                    </button>
                    <pre><code id="code-batch"># Esegui il test suite indicando l'indirizzo del server locale
uv run python test_inference.py --server-url http://{host}:{port}/v1</code></pre>
                </div>
            </div>
        </div>
    </div>
</div>

<footer>
    Local LLM Server &mdash; Generazione specifiche dinamiche
</footer>

<script>
    function switchTab(evt, tabId) {{
        // Hide all panes
        const panes = document.querySelectorAll('.tab-pane');
        panes.forEach(pane => pane.classList.remove('active'));

        // Deactivate all buttons
        const buttons = document.querySelectorAll('.tab-btn');
        buttons.forEach(btn => btn.classList.remove('active'));

        // Show target pane and activate button
        document.getElementById(tabId).classList.add('active');
        evt.currentTarget.classList.add('active');
    }}

    async function copyCode(button) {{
        const pre = button.nextElementSibling;
        const codeText = pre.innerText;

        try {{
            await navigator.clipboard.writeText(codeText);
            button.classList.add('copied');
            button.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="stroke: var(--accent);"><polyline points="20 6 9 17 4 12"></polyline></svg>
                Copied!
            `;

            setTimeout(() => {{
                button.classList.remove('copied');
                button.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    Copy
                `;
            }}, 2000);
        }} catch (err) {{
            console.error('Failed to copy: ', err);
        }}
    }}
</script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.post("/api/v1/models/load", tags=["Models"])
def load_model_compat():
    """LM Studio compatible load endpoint (returns success since model is already loaded)."""
    return {
        "ok": True,
        "model": app.state.cfg["model_id"],
        "already_loaded": True,
    }


@app.post("/api/v1/models/activate", tags=["Models"])
def activate_model(req: ModelActivateRequest):
    """Load and activate a model with optional custom parameters."""
    with app.state.generation_lock:
        try:
            from local_llm_server.config import build_config
            from local_llm_server.engine import load_llm
            
            explicit = {}
            for field_name in [
                "backend", "ctx_size", "n_gpu_layers", "n_threads",
                "n_batch", "n_ubatch", "timeout", "offload_kqv",
                "flash_attn", "use_mmap", "enable_thinking",
                "show_thinking", "verbose", "llama_server_port",
                "llama_server_bin", "mmproj_path", "startup_timeout",
            ]:
                val = getattr(req, field_name)
                if val is not None:
                    explicit[field_name] = val

            current_model_key = app.state.cfg.get("model") if hasattr(app.state, "cfg") and app.state.cfg else None
            model_path_to_use = app.state.cfg.get("model_path") if req.model == current_model_key else None

            new_cfg = build_config(
                model=req.model,
                model_path=model_path_to_use,
                **explicit
            )
            
            # Load the new LLM engine
            new_llm = load_llm(new_cfg)
            old_llm = getattr(app.state, "llm", None)
            
            # If load succeeds, update app.state
            app.state.cfg = new_cfg
            app.state.llm = new_llm
            if old_llm is not None and old_llm is not new_llm and hasattr(old_llm, "shutdown"):
                old_llm.shutdown()
            app.state.current_status.update({
                "model": new_cfg["model_id"]
            })
            
            logger.info("Successfully activated model: %s", req.model)
            return {
                "ok": True,
                "model": new_cfg["model_id"],
                "cfg": {
                    "model": new_cfg["model"],
                    "model_id": new_cfg["model_id"],
                    "model_path": new_cfg["model_path"],
                    "backend": new_cfg["backend"],
                    "mmproj_path": new_cfg.get("mmproj_path"),
                    "llama_server_port": new_cfg.get("llama_server_port"),
                    "ctx_size": new_cfg["ctx_size"],
                    "n_gpu_layers": new_cfg["n_gpu_layers"],
                    "n_threads": new_cfg["n_threads"]
                }
            }
        except Exception as e:
            import traceback
            logger.error("Failed to activate model:\n%s", traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Impossibile caricare il modello '{req.model}': {str(e)}"
            )


@app.post("/api/v1/terminal/run", tags=["System"])
def run_terminal_command(req: TerminalCommandRequest):
    """Execute a terminal command on the host within the current working directory."""
    if not hasattr(app.state, "terminal_cwd"):
        app.state.terminal_cwd = os.getcwd()

    command = req.command.strip()
    if not command:
        return {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "cwd": app.state.terminal_cwd
        }

    # Handle 'cd' statefully
    if command.startswith("cd"):
        parts = shlex.split(command)
        target = "~"
        if len(parts) > 1:
            target = parts[1]
        
        try:
            if target == "~":
                path = os.path.expanduser("~")
            else:
                path = os.path.abspath(os.path.join(app.state.terminal_cwd, target))
            
            if not os.path.exists(path):
                return {
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"cd: no such file or directory: {target}",
                    "cwd": app.state.terminal_cwd
                }
            if not os.path.isdir(path):
                return {
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"cd: not a directory: {target}",
                    "cwd": app.state.terminal_cwd
                }
            
            app.state.terminal_cwd = path
            return {
                "exit_code": 0,
                "stdout": f"Directory cambiata in: {path}",
                "stderr": "",
                "cwd": path
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Errore nel cambio directory: {str(e)}",
                "cwd": app.state.terminal_cwd
            }

    # Run command in the shell under the current working directory
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=app.state.terminal_cwd,
            capture_output=True,
            text=True,
            timeout=15.0
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "cwd": app.state.terminal_cwd
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Errore: Il comando ha superato il timeout di 15 secondi.",
            "cwd": app.state.terminal_cwd
        }
    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Errore durante l'esecuzione: {str(e)}",
            "cwd": app.state.terminal_cwd
        }


# Static Files Serving

@app.get("/", response_class=HTMLResponse, tags=["UI"])
def get_ui():
    """Serve the Web UI dashboard."""
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return FileResponse(static_file)
    raise HTTPException(status_code=404, detail="Web UI file index.html not found.")


@app.get("/static/{path:path}", tags=["UI"])
def get_static_files(path: str):
    """Serve static assets for the Web UI."""
    static_dir = Path(__file__).parent / "static"
    target_file = (static_dir / path).resolve()
    if static_dir in target_file.parents and target_file.exists():
        return FileResponse(target_file)
    raise HTTPException(status_code=404, detail="File not found")


@app.post("/v1/chat/completions", tags=["Inference"])
@app.post("/api/v1/chat", tags=["Inference"])
def chat_completions(req: ChatCompletionRequest):
    """Generate completions for user chat prompts (supports both OpenAI-style and legacy formats)."""
    cfg = app.state.cfg
    started_at = time.perf_counter()

    # Convert request object to payload dict for existing logic
    request_payload = req.dict(exclude_none=True)
    try:
        messages = _normalize_messages(request_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    max_tokens = request_payload.get("max_tokens") or request_payload.get("max_output_tokens")

    # Resolve reasoning/thinking overrides with fallback to model configuration cfg
    req_enable_thinking = request_payload.get("enable_thinking")
    if req_enable_thinking is None:
        req_enable_thinking = request_payload.get("enable_reasoning")
    enable_thinking = req_enable_thinking if req_enable_thinking is not None else cfg.get("enable_thinking", False)

    req_show_thinking = request_payload.get("show_thinking")
    if req_show_thinking is None:
        req_show_thinking = request_payload.get("show_reasoning")
    show_thinking = req_show_thinking if req_show_thinking is not None else cfg.get("show_thinking", False)

    kwargs: dict[str, Any] = {
        "messages": messages,
        "temperature": float(request_payload.get("temperature", cfg.get("default_temperature", 0.0))),
        "top_p": float(request_payload.get("top_p", 1.0)),
        "top_k": int(request_payload.get("top_k", 40)),
        "min_p": float(request_payload.get("min_p", 0.05)),
        "repeat_penalty": float(request_payload.get("repeat_penalty", cfg.get("default_repeat_penalty", 1.1))),
        "presence_penalty": float(request_payload.get("presence_penalty", 0.0)),
        "frequency_penalty": float(request_payload.get("frequency_penalty", 0.0)),
        "stream": True,  # Keep streaming for internal console logs & updates when supported
        "model": str(request_payload.get("model") or cfg["model_id"]),
        "enable_thinking": enable_thinking,
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

    # Handle stream vs non-stream request
    wants_stream = request_payload.get("stream", False)
    if not wants_stream and cfg.get("backend") == "llama_server":
        kwargs["stream"] = False

    def generate_chat_completions_stream():
        with app.state.generation_lock:
            app.state.current_status.update({
                "active": True,
                "phase": "prompt_eval",
                "tokens_generated": 0,
                "max_tokens": int(max_tokens) if max_tokens else 0,
                "started_at": time.perf_counter(),
            })

            try:
                stream = app.state.llm.create_chat_completion(**kwargs)
                print(f"\n\033[94m[{time.strftime('%H:%M:%S')}] LLM inference started | Model: {kwargs['model']} | Messages: {len(messages)} | Temp: {kwargs['temperature']} | Max Tokens: {kwargs.get('max_tokens', 'default')}\033[0m", flush=True)

                is_thinking = False
                is_thinking_for_client = False

                for chunk in stream:
                    if getattr(app.state, "shutdown", False):
                        break
                    if app.state.current_status["phase"] == "prompt_eval":
                        app.state.current_status["phase"] = "generating"
                        app.state.current_status["started_at"] = time.perf_counter()
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

                        app.state.current_status["tokens_generated"] += 1
                        app.state.current_status["last_token_at"] = time.perf_counter()
                        app.state.current_status["last_content"] = (app.state.current_status["last_content"] + token)[-100:]

                    # Handle streaming filtration if show_thinking is False
                    if not show_thinking:
                        client_token = token
                        if is_thinking_for_client:
                            if "</think>" in client_token:
                                parts = client_token.split("</think>", 1)
                                client_token = parts[1]
                                is_thinking_for_client = False
                            else:
                                client_token = ""
                        else:
                            if "<think>" in client_token:
                                is_thinking_for_client = True
                                parts = client_token.split("<think>", 1)
                                before = parts[0]
                                rest = parts[1]
                                if "</think>" in rest:
                                    after = rest.split("</think>", 1)[1]
                                    client_token = before + after
                                    is_thinking_for_client = False
                                else:
                                    client_token = before

                        if client_token:
                            chunk["choices"][0]["delta"]["content"] = client_token
                        else:
                            continue

                    # Yield chunk to client as SSE
                    yield f"data: {json.dumps(chunk)}\n\n"

                elapsed = time.perf_counter() - started_at
                tokens = app.state.current_status["tokens_generated"]
                speed = tokens / elapsed if elapsed > 0 else 0
                print(f"\n\033[92m[Inference complete] Generated {tokens} tokens in {elapsed:.2f}s ({speed:.1f} tokens/s)\033[0m\n", flush=True)
                yield "data: [DONE]\n\n"
            except Exception as e:
                import traceback
                logger.error("Inference stream error:\n%s", traceback.format_exc())
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                app.state.current_status["active"] = False

    if wants_stream:
        return StreamingResponse(generate_chat_completions_stream(), media_type="text/event-stream")

    # Non-streaming request: Reconstruct response from stream generator
    with app.state.generation_lock:
        app.state.current_status.update({
            "active": True,
            "phase": "prompt_eval",
            "tokens_generated": 0,
            "max_tokens": int(max_tokens) if max_tokens else 0,
            "started_at": time.perf_counter(),
        })

        try:
            stream = app.state.llm.create_chat_completion(**kwargs)
            if isinstance(stream, dict):
                return _build_response(
                    stream,
                    model_id=cfg["model_id"],
                    backend=getattr(app.state.llm, "backend", cfg.get("backend", "unknown")),
                    started_at=started_at,
                    finished_at=time.perf_counter(),
                    show_thinking=show_thinking,
                )
            print(f"\n\033[94m[{time.strftime('%H:%M:%S')}] LLM inference started | Model: {kwargs['model']} | Messages: {len(messages)} | Temp: {kwargs['temperature']} | Max Tokens: {kwargs.get('max_tokens', 'default')}\033[0m", flush=True)

            full_content = ""
            raw_response = None
            is_thinking = False

            for chunk in stream:
                if getattr(app.state, "shutdown", False):
                    break
                if app.state.current_status["phase"] == "prompt_eval":
                    app.state.current_status["phase"] = "generating"
                    app.state.current_status["started_at"] = time.perf_counter()
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
                    app.state.current_status["tokens_generated"] += 1
                    app.state.current_status["last_token_at"] = time.perf_counter()
                    app.state.current_status["last_content"] = full_content[-100:]

                if raw_response is None:
                    raw_response = chunk

            elapsed = time.perf_counter() - started_at
            tokens = app.state.current_status["tokens_generated"]
            speed = tokens / elapsed if elapsed > 0 else 0
            print(f"\n\033[92m[Inference complete] Generated {tokens} tokens in {elapsed:.2f}s ({speed:.1f} tokens/s)\033[0m\n", flush=True)

            if raw_response:
                raw_response["choices"][0]["message"] = {"role": "assistant", "content": full_content}
                raw_response["usage"] = {
                    "prompt_tokens": 0,
                    "completion_tokens": app.state.current_status["tokens_generated"],
                    "total_tokens": app.state.current_status["tokens_generated"],
                }

            finished_at = time.perf_counter()
            if raw_response is None:
                raw_response = {
                    "id": "chatcmpl-local-empty",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": cfg["model_id"],
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": full_content}, "finish_reason": "stop"}],
                }

            response = _build_response(
                raw_response,
                model_id=cfg["model_id"],
                backend=getattr(app.state.llm, "backend", cfg.get("backend", "unknown")),
                started_at=started_at,
                finished_at=finished_at,
                show_thinking=show_thinking,
            )
            return response

        except Exception as exc:
            import traceback
            logger.error("Inference error:\n%s", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")
        finally:
            app.state.current_status["active"] = False


# ── Public entry point ──────────────────────────────────────────────────────────

def run_server(cfg: dict[str, Any], llm: Any) -> None:
    """Start the FastAPI uvicorn server."""
    import os
    import uvicorn
    
    # Attach config & engine state to app.state
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

    class CustomUvicornServer(uvicorn.Server):
        def handle_exit(self, sig: int, frame) -> None:
            import time
            print("\n[*] Stopping local-llm-server...", flush=True)
            time.sleep(0.1)
            os._exit(0)

    logger.info(
        "local-llm-server starting on http://%s:%d (model: %s)",
        cfg["host"],
        cfg["port"],
        cfg["model_id"],
    )

    print(f"\n[*] local-llm-server listening on http://{cfg['host']}:{cfg['port']}/v1/chat/completions (model: {cfg['model_id']})", flush=True)
    print(f"[*] 👉 Access Web UI at:       http://{cfg['host']}:{cfg['port']}/", flush=True)
    print(f"[*] 👉 API specifications at:  http://{cfg['host']}:{cfg['port']}/docs", flush=True)
    print(f"[*] 👉 API usage examples at:  http://{cfg['host']}:{cfg['port']}/example\n", flush=True)

    try:
        config = uvicorn.Config(
            app,
            host=cfg["host"],
            port=cfg["port"],
            log_level="warning" if not cfg.get("verbose", False) else "info",
        )
        server = CustomUvicornServer(config)
        server.run()
    except KeyboardInterrupt:
        logger.info("Server uvicorn process interrupted by keyboard event.")
        sys.exit(0)
