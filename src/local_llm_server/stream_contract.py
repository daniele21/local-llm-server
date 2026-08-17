"""Backend-neutral stream shape normalization.

The historical HTTP route ignores chunks whose ``choices`` collection is empty.
Modern backends may legitimately emit terminal usage/timing evidence without
text. This wrapper adds an empty OpenAI-compatible choice only to those evidence
chunks so the route transports them unchanged to the product telemetry layer.
It never invents token/timing values or generated text.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


class StreamContractEngine:
    """Delegate an engine while preserving metrics-only streaming events."""

    _local_llm_stream_contract = True

    def __init__(self, engine: Any) -> None:
        self._engine = engine
        self.backend = getattr(engine, "backend", "unknown")

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._engine.complete(payload)

    def stream(self, payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
        for chunk in self._engine.stream(payload):
            if not isinstance(chunk, Mapping):
                yield chunk
                continue
            normalized = dict(chunk)
            choices = normalized.get("choices")
            has_choices = isinstance(choices, list) and bool(choices)
            has_evidence = any(
                isinstance(normalized.get(key), Mapping) and bool(normalized.get(key))
                for key in ("usage", "timings")
            )
            if not has_choices and has_evidence:
                normalized["choices"] = [
                    {"index": 0, "delta": {}, "finish_reason": None}
                ]
            yield normalized

    def close(self) -> None:
        close = getattr(self._engine, "close", None) or getattr(self._engine, "shutdown", None)
        if close is not None:
            close()

    shutdown = close

    def __getattr__(self, name: str) -> Any:
        return getattr(self._engine, name)


def ensure_stream_contract(engine: Any) -> Any:
    if getattr(engine, "_local_llm_stream_contract", False):
        return engine
    return StreamContractEngine(engine)
