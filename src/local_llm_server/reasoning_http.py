"""ASGI reasoning boundary for streamed chat responses.

Hidden reasoning is redacted after the inner streaming-metrics middleware has
observed the raw route stream. The middleware rewrites only the private inbound
``show_thinking`` value for streamed requests so the legacy route transports raw
model content; the outer boundary then applies one chunk-safe state machine
immediately before bytes reach the client.
"""
from __future__ import annotations

import codecs
import json
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI

from .reasoning_boundary import ReasoningStreamParser

_INFERENCE_PATHS = frozenset({"/v1/chat/completions", "/api/v1/chat"})


class ReasoningBoundaryMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or scope.get("method", "").upper() != "POST":
            await self.app(scope, receive, send)
            return
        if scope.get("path") not in _INFERENCE_PATHS:
            await self.app(scope, receive, send)
            return

        body = await _read_request_body(receive)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            await self.app(scope, _replay_body(body, receive), send)
            return
        if not isinstance(payload, dict) or not bool(payload.get("stream", False)):
            await self.app(scope, _replay_body(body, receive), send)
            return

        application = scope.get("app")
        manager = getattr(getattr(application, "state", None), "runtime_manager", None)
        runtime = None
        if manager is not None:
            try:
                runtime = manager.resolve(payload.get("model"))
            except (LookupError, RuntimeError):
                runtime = None
        cfg = getattr(runtime, "cfg", {}) if runtime is not None else {}

        show_thinking = _effective_bool(
            payload,
            primary="show_thinking",
            alias="show_reasoning",
            fallback=cfg.get("show_thinking", False),
        )
        if show_thinking:
            await self.app(scope, _replay_body(body, receive), send)
            return

        enable_thinking = _effective_bool(
            payload,
            primary="enable_thinking",
            alias="enable_reasoning",
            fallback=cfg.get("enable_thinking", False),
        )
        if str(cfg.get("thinking_mode", "none")) == "always":
            enable_thinking = True

        downstream = dict(payload)
        downstream["show_thinking"] = True
        downstream.pop("show_reasoning", None)
        rewritten = json.dumps(
            downstream,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        rewritten_scope = dict(scope)
        rewritten_scope["headers"] = _replace_content_length(
            scope.get("headers", []), len(rewritten)
        )

        redactor = SSEReasoningRedactor(expect_reasoning=enable_thinking)

        async def filtered_send(message: dict[str, Any]) -> None:
            if message.get("type") != "http.response.body":
                await send(message)
                return

            chunk = message.get("body", b"") or b""
            more_body = bool(message.get("more_body", False))
            output = redactor.feed(chunk)
            if not more_body:
                output += redactor.finish()
            if output or not more_body:
                forwarded = dict(message)
                forwarded["body"] = output
                await send(forwarded)

        await self.app(
            rewritten_scope,
            _replay_body(rewritten, receive),
            filtered_send,
        )


class SSEReasoningRedactor:
    """Remove reasoning from OpenAI-compatible SSE without losing metadata."""

    def __init__(self, *, expect_reasoning: bool) -> None:
        self.parser = ReasoningStreamParser(expect_reasoning=expect_reasoning)
        self._decoder = codecs.getincrementaldecoder("utf-8")()
        self._buffer = ""
        self._last_metadata: dict[str, Any] = {}
        self._done_seen = False

    def feed(self, chunk: bytes | str) -> bytes:
        if isinstance(chunk, bytes):
            text = self._decoder.decode(chunk, final=False)
        else:
            text = str(chunk)
        self._buffer += text
        output: list[str] = []

        while "\n\n" in self._buffer:
            event, self._buffer = self._buffer.split("\n\n", 1)
            rendered = self._filter_event(event)
            if rendered:
                output.append(rendered + "\n\n")
        return "".join(output).encode("utf-8")

    def finish(self) -> bytes:
        self._buffer += self._decoder.decode(b"", final=True)
        output: list[str] = []
        if self._buffer:
            rendered = self._filter_event(self._buffer.rstrip("\n"))
            if rendered:
                output.append(rendered + "\n\n")
            self._buffer = ""
        if not self._done_seen:
            tail = self.parser.finish()
            if tail:
                output.append(self._synthetic_content_event(tail) + "\n\n")
        return "".join(output).encode("utf-8")

    def _filter_event(self, event: str) -> str:
        stripped = event.strip()
        if not stripped or not stripped.startswith("data:"):
            return event
        data = stripped[5:].strip()
        if data == "[DONE]":
            tail = self.parser.finish()
            self._done_seen = True
            if tail:
                return self._synthetic_content_event(tail) + "\n\ndata: [DONE]"
            return "data: [DONE]"

        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return event
        if not isinstance(payload, dict):
            return event

        self._remember_metadata(payload)
        choices = payload.get("choices")
        exposed_content = False
        removed_content = False
        has_noncontent_signal = _has_noncontent_signal(payload)
        if isinstance(choices, list):
            normalized_choices: list[Any] = []
            for choice in choices:
                if not isinstance(choice, dict):
                    normalized_choices.append(choice)
                    continue
                normalized = dict(choice)
                delta = normalized.get("delta")
                if isinstance(delta, dict):
                    normalized_delta = dict(delta)
                    content = normalized_delta.get("content")
                    if isinstance(content, str) and content:
                        exposed = self.parser.feed(content)
                        if exposed:
                            normalized_delta["content"] = exposed
                            exposed_content = True
                        else:
                            normalized_delta.pop("content", None)
                            removed_content = True
                    normalized["delta"] = normalized_delta
                normalized_choices.append(normalized)
            payload["choices"] = normalized_choices

        if removed_content and not exposed_content and not has_noncontent_signal:
            return ""
        return "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    def _remember_metadata(self, payload: Mapping[str, Any]) -> None:
        for key in ("id", "object", "created", "model"):
            if key in payload:
                self._last_metadata[key] = payload[key]

    def _synthetic_content_event(self, content: str) -> str:
        payload = dict(self._last_metadata)
        payload.setdefault("object", "chat.completion.chunk")
        payload["choices"] = [
            {
                "index": 0,
                "delta": {"content": content},
                "finish_reason": None,
            }
        ]
        return "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def install_reasoning_boundary(application: FastAPI) -> FastAPI:
    if getattr(application.state, "reasoning_boundary_installed", False):
        return application
    application.state.reasoning_boundary_installed = True
    application.add_middleware(ReasoningBoundaryMiddleware)
    return application


async def _read_request_body(receive: Any) -> bytes:
    chunks: list[bytes] = []
    more_body = True
    while more_body:
        message = await receive()
        if message.get("type") != "http.request":
            continue
        chunks.append(message.get("body", b"") or b"")
        more_body = bool(message.get("more_body", False))
    return b"".join(chunks)


def _replay_body(body: bytes, original_receive: Any):
    """Replay the consumed body once, then preserve the real disconnect channel."""
    sent = False

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        # StreamingResponse listens for a genuine client disconnect while the
        # body iterator runs. Fabricating ``http.disconnect`` here cancels the
        # stream after its first chunk; delegate to the original ASGI receive
        # channel so only a real disconnect terminates the response.
        return await original_receive()

    return receive


def _replace_content_length(headers: Any, length: int) -> list[tuple[bytes, bytes]]:
    output: list[tuple[bytes, bytes]] = []
    for key, value in headers:
        if bytes(key).lower() == b"content-length":
            continue
        output.append((bytes(key), bytes(value)))
    output.append((b"content-length", str(length).encode("ascii")))
    return output


def _effective_bool(
    payload: Mapping[str, Any],
    *,
    primary: str,
    alias: str,
    fallback: Any,
) -> bool:
    value = payload.get(primary)
    if value is None:
        value = payload.get(alias)
    if value is None:
        value = fallback
    return bool(value)


def _has_noncontent_signal(payload: Mapping[str, Any]) -> bool:
    if isinstance(payload.get("usage"), Mapping) and payload.get("usage"):
        return True
    if isinstance(payload.get("timings"), Mapping) and payload.get("timings"):
        return True
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return False
    for choice in choices:
        if not isinstance(choice, Mapping):
            continue
        if choice.get("finish_reason") is not None:
            return True
        delta = choice.get("delta")
        if isinstance(delta, Mapping) and any(key != "content" for key in delta):
            return True
    return False
