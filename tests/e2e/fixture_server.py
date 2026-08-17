from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

import uvicorn

import local_llm_server
from local_llm_server.capability_catalog import capability_catalog_item
from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.server import ServerSettings, create_app

MODEL_KEY = "e2e-switchable"
MODEL_ID = "org/e2e-switchable"
ALT_MODEL_KEY = "e2e-alt"
ALT_MODEL_ID = "org/e2e-alt"


def _runtime_config(model_key: str, model_id: str) -> dict[str, Any]:
    return {
        "model": model_key,
        "model_id": model_id,
        "model_path": f"/e2e/{model_key}.gguf",
        "backend": "llama_cpp",
        "modalities": ["text"],
        "thinking_mode": "switchable",
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
        "default_temperature": 0.0,
        "default_top_p": 1.0,
        "default_top_k": 40,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "max_concurrent_requests": 1,
    }


def _structured(payload: dict[str, Any]) -> bool:
    response_format = payload.get("response_format")
    return isinstance(response_format, dict) and response_format.get("type") in {
        "json_object",
        "json_schema",
    }


def _last_user_text(payload: dict[str, Any]) -> str:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return content
    return ""


def _answer(payload: dict[str, Any], answer: int) -> str:
    final = f'{{"answer":{answer}}}' if _structured(payload) else str(answer)
    if payload.get("enable_thinking") is True:
        return f"<think>private reasoning</think>{final}"
    return final


def _stream_event(
    model_id: str,
    content: str | None = None,
    *,
    finish_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "id": "chatcmpl-e2e",
        "object": "chat.completion.chunk",
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "delta": {} if content is None else {"content": content},
                "finish_reason": finish_reason,
            }
        ],
    }


class DeterministicBrowserEngine:
    backend = "llama_cpp"
    backend_version = "e2e-fixture"

    def __init__(self, model_id: str, answer: int) -> None:
        self.model_id = model_id
        self.answer = answer

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "chatcmpl-e2e",
            "object": "chat.completion",
            "model": self.model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": _answer(payload, self.answer),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 4, "completion_tokens": 4, "total_tokens": 8},
        }

    def stream(self, payload: dict[str, Any]):
        final = f'{{"answer":{self.answer}}}' if _structured(payload) else str(self.answer)
        slow = "[slow-status]" in _last_user_text(payload)
        if payload.get("enable_thinking") is True:
            chunks = ("<thi", "nk>private reasoning", "</th", f"ink>{final}")
        elif slow and len(final) > 1:
            chunks = tuple(final)
        else:
            chunks = (final,)
        for index, content in enumerate(chunks):
            yield _stream_event(self.model_id, content)
            if slow and index == 0:
                # Keep the request genuinely active long enough for the browser's
                # 300 ms /status polling loop to observe the generating phase.
                time.sleep(0.8)
        yield _stream_event(self.model_id, None, finish_reason="stop")

    def close(self) -> None:
        return None


def _catalog_item(model_key: str, model_id: str) -> dict[str, Any]:
    cfg = _runtime_config(model_key, model_id)
    capability = capability_catalog_item(model_key, cfg)
    return {
        "key": model_key,
        "model_id": model_id,
        "size_gb": 0.0,
        "tags": ["e2e"],
        "backend": "llama_cpp",
        "multimodal": False,
        "modalities": ["text"],
        "capabilities": capability["capabilities"],
        "capability_source": capability["capability_source"],
        "downloaded": True,
        "path": f"/e2e/{model_key}.gguf",
        "source": "e2e-fixture",
        "mmproj_path": None,
    }


def build_app():
    # The registry route imports this symbol at request time. Replacing it here
    # keeps the browser fixture deterministic without touching user model files.
    local_llm_server.list_models = lambda: [
        _catalog_item(MODEL_KEY, MODEL_ID),
        _catalog_item(ALT_MODEL_KEY, ALT_MODEL_ID),
    ]

    manager = ProductRuntimeManager(default_model=MODEL_KEY)
    manager.add(
        _runtime_config(MODEL_KEY, MODEL_ID),
        DeterministicBrowserEngine(MODEL_ID, 42),
    )
    manager.add(
        _runtime_config(ALT_MODEL_KEY, ALT_MODEL_ID),
        DeterministicBrowserEngine(ALT_MODEL_ID, 84),
    )
    application = create_app(
        manager,
        settings=ServerSettings(enable_admin_api=True),
    )
    evaluation_root = Path(tempfile.mkdtemp(prefix="local-llm-e2e-evaluation-"))
    install_product_http_stack(application, evaluation_root=evaluation_root)
    return application


app = build_app()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
