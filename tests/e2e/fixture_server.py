from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any

import uvicorn

import local_llm_server
from local_llm_server.capability_catalog import capability_catalog_item
from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.product_runtime_manager import ProductRuntimeManager
from local_llm_server.server import ServerSettings, create_app

from lifecycle import OwnedRunState

MODEL_KEY = "e2e-switchable"
MODEL_ID = "org/e2e-switchable"
ALT_MODEL_KEY = "e2e-alt"
ALT_MODEL_ID = "org/e2e-alt"
ASR_MODEL_KEY = "e2e-asr"
ASR_MODEL_ID = "org/e2e-asr"
HOST = "127.0.0.1"
PORT = 8765


def _runtime_config(
    model_key: str,
    model_id: str,
    *,
    modalities: list[str] | None = None,
    tasks: list[str] | None = None,
) -> dict[str, Any]:
    resolved_modalities = list(modalities or ["text"])
    cfg: dict[str, Any] = {
        "model": model_key,
        "model_id": model_id,
        "model_path": f"/e2e/{model_key}.gguf",
        "backend": "llama_cpp",
        "modalities": resolved_modalities,
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
    if tasks:
        cfg["tasks"] = list(tasks)
    return cfg


def _asr_runtime_config() -> dict[str, Any]:
    return {
        "model": ASR_MODEL_KEY,
        "model_id": ASR_MODEL_ID,
        "model_path": f"/e2e/{ASR_MODEL_KEY}",
        "backend": "fake_asr",
        "modalities": ["audio", "text"],
        "tasks": ["transcription"],
        "input_modalities": ["audio"],
        "output_modalities": ["text"],
        "max_concurrent_requests": 1,
    }


def _structured(payload: dict[str, Any]) -> bool:
    response_format = payload.get("response_format")
    return isinstance(response_format, dict) and response_format.get("type") in {"json_object", "json_schema"}


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


def _stream_event(model_id: str, content: str | None = None, *, finish_reason: str | None = None) -> dict[str, Any]:
    return {
        "id": "chatcmpl-e2e",
        "object": "chat.completion.chunk",
        "model": model_id,
        "choices": [{"index": 0, "delta": {} if content is None else {"content": content}, "finish_reason": finish_reason}],
    }


class DeterministicBrowserEngine:
    backend = "llama_cpp"
    backend_version = "e2e-fixture"

    def __init__(self, model_id: str, answer: int) -> None:
        self.model_id = model_id
        self.answer = answer

    def _raise_if_requested(self, payload: dict[str, Any]) -> None:
        if "[backend-error]" in _last_user_text(payload):
            raise RuntimeError("deterministic fixture backend failure")

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._raise_if_requested(payload)
        return {
            "id": "chatcmpl-e2e",
            "object": "chat.completion",
            "model": self.model_id,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": _answer(payload, self.answer)}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 4, "total_tokens": 8},
        }

    def stream(self, payload: dict[str, Any]):
        self._raise_if_requested(payload)
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
                time.sleep(0.8)
        yield _stream_event(self.model_id, None, finish_reason="stop")

    def close(self) -> None:
        return None


class DeterministicAsrEngine:
    backend = "fake_asr"
    backend_version = "e2e-fixture"

    def transcribe(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "text": "deterministic transcript",
            "language": payload.get("language") or "en",
            "duration": 1.25,
            "segments": [
                {"start": 0.0, "end": 1.25, "text": "deterministic transcript"}
            ],
        }

    def close(self) -> None:
        return None


def _catalog_item(cfg: dict[str, Any]) -> dict[str, Any]:
    model_key = str(cfg["model"])
    model_id = str(cfg["model_id"])
    modalities = list(cfg.get("modalities") or ["text"])
    capability = capability_catalog_item(model_key, cfg)
    return {
        "key": model_key,
        "model_id": model_id,
        "size_gb": 0.0,
        "tags": ["e2e"],
        "backend": cfg.get("backend", "llama_cpp"),
        "multimodal": len(set(modalities)) > 1,
        "modalities": modalities,
        "capabilities": capability["capabilities"],
        "capability_source": capability["capability_source"],
        "downloaded": True,
        "path": f"/e2e/{model_key}.gguf",
        "source": "e2e-fixture",
        "mmproj_path": None,
    }


def _owned_run_state_from_environment() -> OwnedRunState:
    run_id = os.environ.get("LOCAL_LLM_E2E_RUN_ID")
    root = os.environ.get("LOCAL_LLM_E2E_ROOT")
    if not run_id or not root:
        raise RuntimeError("fixture_server.py must be started by fixture_runner.py")
    state = OwnedRunState(run_id=run_id, root=Path(root))
    if not state.owns_root():
        raise RuntimeError(f"invalid or unowned E2E run root: {state.root}")
    if not state.evaluation_root.is_dir():
        raise RuntimeError(f"missing E2E evaluation root: {state.evaluation_root}")
    return state


def build_app(run_state: OwnedRunState):
    text_cfg = _runtime_config(MODEL_KEY, MODEL_ID)
    vision_cfg = _runtime_config(
        ALT_MODEL_KEY,
        ALT_MODEL_ID,
        modalities=["text", "image"],
    )
    asr_cfg = _asr_runtime_config()
    catalog = [text_cfg, vision_cfg, asr_cfg]
    local_llm_server.list_models = lambda: [_catalog_item(cfg) for cfg in catalog]

    manager = ProductRuntimeManager(default_model=MODEL_KEY)
    manager.add(text_cfg, DeterministicBrowserEngine(MODEL_ID, 42))
    manager.add(vision_cfg, DeterministicBrowserEngine(ALT_MODEL_ID, 84))
    manager.add(asr_cfg, DeterministicAsrEngine())
    application = create_app(manager, settings=ServerSettings(enable_admin_api=True))
    install_product_http_stack(application, evaluation_root=run_state.evaluation_root)
    application.state.e2e_run_id = run_state.run_id
    application.state.e2e_root = str(run_state.root)
    return application


RUN_STATE = _owned_run_state_from_environment()
app = build_app(RUN_STATE)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        timeout_graceful_shutdown=3,
    )
