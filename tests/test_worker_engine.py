from __future__ import annotations

from pathlib import Path

import pytest

from local_llm_server.worker_engine import WorkerBackedEngine, _json_safe
from local_llm_server.worker_protocol import WorkerCommand, WorkerResponse, WorkerState


class _FakeTransport:
    instances = []

    def __init__(self, command, *, env=None):
        self.command = tuple(command)
        self.env = dict(env or {})
        self.started = []
        self.stopped = []
        self.requests = []
        self.prepare_accepted = True
        self.generation_result = {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1},
        }
        type(self).instances.append(self)

    def start(self, *, timeout):
        self.started.append(timeout)
        return WorkerResponse("start", True, WorkerState.READY)

    def request(self, command, payload=None, *, timeout):
        self.requests.append((command, payload or {}, timeout))
        if command is WorkerCommand.PREPARE:
            return WorkerResponse(
                "prepare",
                self.prepare_accepted,
                WorkerState.READY,
                error_code=None if self.prepare_accepted else "prepare_failed",
                details={"prepared": self.prepare_accepted, "backend": "fake"},
            )
        if command is WorkerCommand.GENERATE:
            return WorkerResponse(
                "generate",
                True,
                WorkerState.READY,
                details={"result": self.generation_result},
            )
        if command is WorkerCommand.HEALTH:
            return WorkerResponse(
                "health",
                True,
                WorkerState.READY,
                details={"prepared": True, "backend": "fake"},
            )
        raise AssertionError(f"unexpected command: {command}")

    def stop(self, *, timeout):
        self.stopped.append(timeout)


def _cfg():
    return {
        "model": "demo",
        "model_id": "org/demo",
        "model_path": Path("/private/models/demo.gguf"),
        "backend": "fake",
        "startup_timeout": 3,
        "timeout": 20,
    }


def test_worker_backed_engine_starts_prepares_and_executes_completed_response():
    _FakeTransport.instances.clear()
    engine = WorkerBackedEngine(_cfg(), transport_factory=_FakeTransport)
    transport = _FakeTransport.instances[-1]

    assert transport.command[-2:] == ("-m", "local_llm_server.worker_entrypoint")
    assert transport.started == [3.0]
    assert transport.requests[0][0] is WorkerCommand.PREPARE
    prepared_config = transport.requests[0][1]["config"]
    assert prepared_config["model_path"] == "/private/models/demo.gguf"

    result = engine.complete({"messages": [{"role": "user", "content": "hi"}]})

    assert result["usage"]["completion_tokens"] == 1
    generate_command, generate_payload, timeout = transport.requests[-1]
    assert generate_command is WorkerCommand.GENERATE
    assert generate_payload["stream"] is False
    assert generate_payload["request"]["messages"][0]["content"] == "hi"
    assert timeout == 20.0

    health = engine.health()
    assert health == {
        "accepted": True,
        "state": "ready",
        "prepared": True,
        "backend": "fake",
    }

    engine.close()
    assert transport.stopped == [5.0]


def test_worker_backed_engine_does_not_fake_streaming_support():
    _FakeTransport.instances.clear()
    engine = WorkerBackedEngine(_cfg(), transport_factory=_FakeTransport)

    assert engine.supports_streaming is False
    assert engine.execution_isolation == "subprocess_worker"
    with pytest.raises(RuntimeError, match="streaming is not supported"):
        engine.stream({"messages": []})

    engine.close()


def test_prepare_failure_stops_worker_before_raising():
    class _PrepareFailTransport(_FakeTransport):
        def __init__(self, command, *, env=None):
            super().__init__(command, env=env)
            self.prepare_accepted = False

    _PrepareFailTransport.instances.clear()

    with pytest.raises(RuntimeError, match="prepare_failed"):
        WorkerBackedEngine(_cfg(), transport_factory=_PrepareFailTransport)

    transport = _PrepareFailTransport.instances[-1]
    assert transport.stopped == [3.0]


def test_invalid_worker_completion_shape_is_rejected():
    class _InvalidResultTransport(_FakeTransport):
        def __init__(self, command, *, env=None):
            super().__init__(command, env=env)
            self.generation_result = "not-a-mapping"

    _InvalidResultTransport.instances.clear()
    engine = WorkerBackedEngine(_cfg(), transport_factory=_InvalidResultTransport)

    with pytest.raises(RuntimeError, match="invalid completion result"):
        engine.complete({"messages": []})

    engine.close()


def test_json_safe_preserves_data_shape_without_executable_objects():
    value = {
        "path": Path("/tmp/model"),
        "command": WorkerCommand.GENERATE,
        "nested": (1, {"state": WorkerState.READY}),
    }

    assert _json_safe(value) == {
        "path": "/tmp/model",
        "command": "generate",
        "nested": [1, {"state": "ready"}],
    }
