from __future__ import annotations

import tempfile
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


def _runtime_config() -> dict[str, Any]:
    return {
        "model": MODEL_KEY,
        "model_id": MODEL_ID,
        "model_path": "/e2e/model.gguf",
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


def _answer(payload: dict[str, Any]) -> str:
    final = '{"answer":42}' if _structured(payload) else "42"
    if payload.get("enable_thinking") is True:
        return f"<think>private reasoning</think>{final}"
    return final


def _stream_event(content: str | None = None, *, finish_reason: str | None = None) -> dict[str, Any]:
    return {
        "id": "chatcmpl-e2e",
        "object": "chat.completion.chunk",
        "model": MODEL_ID,
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

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "chatcmpl-e2e",
            "object": "chat.completion",
            "model": MODEL_ID,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": _answer(payload)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 4, "completion_tokens": 4, "total_tokens": 8},
        }

    def stream(self, payload: dict[str, Any]):
        final = '{"answer":42}' if _structured(payload) else "42"
        if payload.get("enable_thinking") is True:
            for content in ("<thi", "nk>private reasoning", "</th", f"ink>{final}"):
                yield _stream_event(content)
        else:
            yield _stream_event(final)
        yield _stream_event(None, finish_reason="stop")

    def close(self) -> None:
        return None


def _catalog_item() -> dict[str, Any]:
    cfg = _runtime_config()
    capability = capability_catalog_item(MODEL_KEY, cfg)
    return {
        "key": MODEL_KEY,
        "model_id": MODEL_ID,
        "size_gb": 0.0,
        "tags": ["e2e"],
        "backend": "llama_cpp",
        "multimodal": False,
        "modalities": ["text"],
        "capabilities": capability["capabilities"],
        "capability_source": capability["capability_source"],
        "downloaded": True,
        "path": "/e2e/model.gguf",
        "source": "e2e-fixture",
        "mmproj_path": None,
    }


def build_app():
    # The registry route imports this symbol at request time. Replacing it here
    # keeps the browser fixture deterministic without touching user model files.
    local_llm_server.list_models = lambda: [_catalog_item()]

    manager = ProductRuntimeManager(default_model=MODEL_KEY)
    manager.add(_runtime_config(), DeterministicBrowserEngine())
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
