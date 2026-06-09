"""
server.py — OpenAI-compatible HTTP server built on FastAPI.
Provides automatically generated interactive OpenAPI documentation at /docs.
"""
from __future__ import annotations

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
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
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
            self.listeners = [l for l in self.listeners if not getattr(l, "closed", False)]
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

    def write(self, text: str) -> None:
        self.original.write(text)
        self.original.flush()
        if text.strip():
            self.buffer.append(text.rstrip("\r\n"))

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
    description="OpenAI-compatible API serving local LLMs (Llama-cpp, MLX).",
    version="0.1.0",
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
def stream_logs():
    """SSE endpoint streaming live console logs of the server process."""
    def log_generator():
        q = log_buffer.add_listener()
        try:
            while True:
                try:
                    msg = q.get(timeout=1.0)
                    lines = msg.splitlines()
                    for line in lines:
                        yield f"data: {line}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
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

    kwargs: dict[str, Any] = {
        "messages": messages,
        "temperature": float(request_payload.get("temperature", cfg.get("default_temperature", 0.0))),
        "top_p": float(request_payload.get("top_p", 1.0)),
        "top_k": int(request_payload.get("top_k", 40)),
        "min_p": float(request_payload.get("min_p", 0.05)),
        "repeat_penalty": float(request_payload.get("repeat_penalty", 1.0)),
        "presence_penalty": float(request_payload.get("presence_penalty", 0.0)),
        "frequency_penalty": float(request_payload.get("frequency_penalty", 0.0)),
        "stream": True,  # Keep streaming for internal console logs & updates
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

    # Handle stream vs non-stream request
    wants_stream = request_payload.get("stream", False)

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
                for chunk in stream:
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
            print(f"\n\033[94m[{time.strftime('%H:%M:%S')}] LLM inference started | Model: {kwargs['model']} | Messages: {len(messages)} | Temp: {kwargs['temperature']} | Max Tokens: {kwargs.get('max_tokens', 'default')}\033[0m", flush=True)

            full_content = ""
            raw_response = None
            is_thinking = False

            for chunk in stream:
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
            response = _build_response(
                raw_response,
                model_id=cfg["model_id"],
                backend=getattr(app.state.llm, "backend", cfg.get("backend", "unknown")),
                started_at=started_at,
                finished_at=finished_at,
                show_thinking=cfg["show_thinking"],
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
    import uvicorn
    
    # Attach config & engine state to app.state
    app.state.cfg = cfg
    app.state.llm = llm
    app.state.generation_lock = threading.Lock()
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

    uvicorn.run(
        app,
        host=cfg["host"],
        port=cfg["port"],
        log_level="warning" if not cfg.get("verbose", False) else "info",
    )
