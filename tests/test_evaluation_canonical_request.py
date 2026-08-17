from __future__ import annotations

from dataclasses import replace

from local_llm_server.backend_request import build_backend_request
from local_llm_server.core.contracts import (
    GenerationOptions,
    InferenceRequest,
    OutputConstraints,
    TaskType,
)
from local_llm_server.evaluation_service import ResidentRuntimeExecutor
from local_llm_server.runtime import ModelRuntimeManager


class _CaptureEngine:
    backend = "fake"

    def __init__(self):
        self.payloads = []

    def complete(self, payload):
        self.payloads.append(dict(payload))
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": '{"ok": true}'},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"completion_tokens": 3},
        }

    def close(self):
        pass


def _runtime():
    engine = _CaptureEngine()
    cfg = {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": "/demo",
        "backend": "fake",
        "thinking_mode": "none",
        "default_temperature": 0.2,
        "default_top_p": 0.8,
        "default_top_k": 20,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "max_concurrent_requests": 1,
    }
    manager = ModelRuntimeManager(default_model="demo")
    runtime = manager.add(cfg, engine)
    return manager, runtime, engine


def test_evaluation_executor_uses_exact_canonical_backend_preparation():
    manager, runtime, engine = _runtime()
    request = InferenceRequest(
        task=TaskType.STRUCTURED_GENERATION,
        model="demo",
        input_text="return an object",
        generation=GenerationOptions(
            max_tokens=64,
            temperature=0.0,
            top_p=0.7,
            top_k=8,
            seed=11,
        ),
        output=OutputConstraints(format="json_object"),
    )
    canonical = replace(
        request,
        messages=({"role": "user", "content": "return an object"},),
    )
    expected = build_backend_request(
        canonical,
        runtime_config=runtime.cfg,
        runtime_model_id=runtime.model_id,
    )

    ResidentRuntimeExecutor(manager, runtime=runtime).execute(request)

    assert engine.payloads == [dict(expected.kwargs)]
    assert engine.payloads[0]["response_format"] == {"type": "json_object"}
    assert engine.payloads[0]["temperature"] == 0.0
    assert engine.payloads[0]["seed"] == 11


def test_pinned_evaluation_executor_does_not_reresolve_runtime(monkeypatch):
    manager, runtime, engine = _runtime()
    executor = ResidentRuntimeExecutor(manager, runtime=runtime)
    monkeypatch.setattr(
        manager,
        "resolve",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected resolve")),
    )

    executor.execute(
        InferenceRequest(
            task=TaskType.CHAT,
            model="demo",
            input_text="hello",
            generation=GenerationOptions(temperature=0.0),
        )
    )

    assert len(engine.payloads) == 1
