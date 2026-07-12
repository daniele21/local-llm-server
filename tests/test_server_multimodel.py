from __future__ import annotations

import threading

import pytest
from fastapi import HTTPException

from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.server import ChatCompletionRequest, chat_completions, configure_runtime


class _Engine:
    backend = "fake"

    def __init__(self, content: str, barrier: threading.Barrier | None = None):
        self.content = content
        self.barrier = barrier
        self.received_model = None

    def create_chat_completion(self, **kwargs):
        self.received_model = kwargs["model"]
        if self.barrier:
            self.barrier.wait(timeout=2)
        return {
            "choices": [{"index": 0, "message": {"role": "assistant", "content": self.content}}],
            "usage": {"completion_tokens": 1},
        }

    def shutdown(self):
        pass


def _cfg(key: str, model_id: str):
    return {
        "model": key,
        "model_id": model_id,
        "model_path": f"/{key}",
        "backend": "fake",
        "host": "127.0.0.1",
        "port": 1235,
        "default_temperature": 0.0,
        "default_repeat_penalty": 1.1,
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
    }


def _install_manager(first_engine, second_engine):
    first_cfg = _cfg("text", "org/text")
    second_cfg = _cfg("vision", "org/vision")
    manager = ModelRuntimeManager(default_model="text")
    manager.add(first_cfg, first_engine)
    manager.add(second_cfg, second_engine)
    configure_runtime(first_cfg, first_engine, manager)
    return manager


def test_chat_routes_to_requested_resident_model():
    text = _Engine("text response")
    vision = _Engine("vision response")
    _install_manager(text, vision)

    response = chat_completions(
        ChatCompletionRequest(
            model="vision",
            messages=[{"role": "user", "content": "describe"}],
            stream=False,
        )
    )

    assert response["content"] == "vision response"
    assert vision.received_model == "org/vision"
    assert text.received_model is None


def test_chat_without_model_uses_default_runtime():
    text = _Engine("default response")
    vision = _Engine("vision response")
    _install_manager(text, vision)

    response = chat_completions(
        ChatCompletionRequest(messages=[{"role": "user", "content": "hello"}], stream=False)
    )

    assert response["content"] == "default response"
    assert text.received_model == "org/text"


def test_chat_rejects_model_that_is_not_resident():
    _install_manager(_Engine("text"), _Engine("vision"))

    with pytest.raises(HTTPException) as exc_info:
        chat_completions(
            ChatCompletionRequest(
                model="missing",
                messages=[{"role": "user", "content": "hello"}],
                stream=False,
            )
        )

    assert exc_info.value.status_code == 404


def test_requests_for_different_models_run_in_parallel():
    barrier = threading.Barrier(2)
    _install_manager(_Engine("text", barrier), _Engine("vision", barrier))
    responses = []

    def request(model):
        responses.append(
            chat_completions(
                ChatCompletionRequest(
                    model=model,
                    messages=[{"role": "user", "content": "go"}],
                    stream=False,
                )
            )["content"]
        )

    threads = [threading.Thread(target=request, args=(model,)) for model in ("text", "vision")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert sorted(responses) == ["text", "vision"]
