"""Request-level llama-cpp-python chat-template controls.

``Llama.create_chat_completion`` does not expose arbitrary template variables as
request parameters. Metadata-backed Jinja chat handlers do: their handler
contract accepts extra kwargs and forwards them to the formatter/template.
This adapter uses that proven handler path for switchable thinking without
mutating the loaded model or forwarding unknown kwargs to the public completion
method.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterator


class LlamaCppThinkingControlError(RuntimeError):
    """The loaded llama.cpp chat path cannot prove request-level control."""


def chat_completion(
    llm: Any,
    payload: Mapping[str, Any],
    *,
    stream: bool,
) -> dict[str, Any] | Iterator[dict[str, Any]]:
    kwargs = dict(payload)
    requested = kwargs.pop("enable_thinking", None)
    kwargs["stream"] = stream

    if requested is None:
        return llm.create_chat_completion(**kwargs)

    handler = _metadata_template_handler(llm)
    try:
        return handler(
            llama=llm,
            **kwargs,
            enable_thinking=bool(requested),
        )
    except TypeError as exc:
        raise LlamaCppThinkingControlError(
            "The selected llama_cpp chat handler cannot accept request-level "
            "thinking template variables."
        ) from exc


def _metadata_template_handler(llm: Any) -> Any:
    """Return only a metadata-backed Jinja handler we can reason about safely.

    llama-cpp-python builds ``_chat_handlers`` from GGUF tokenizer chat-template
    metadata. Those Jinja handlers forward arbitrary kwargs into the template.
    Custom/pre-registered handlers are deliberately not guessed to support the
    variable: a runtime advertising switchability must use a path we can prove.
    """
    chat_format = getattr(llm, "chat_format", None)
    handlers = getattr(llm, "_chat_handlers", None)
    if isinstance(chat_format, str) and isinstance(handlers, Mapping):
        handler = handlers.get(chat_format)
        if callable(handler):
            return handler

    raise LlamaCppThinkingControlError(
        "Request-level llama_cpp thinking requires a GGUF metadata-backed "
        "Jinja chat template. The selected chat handler is not provably switchable."
    )
