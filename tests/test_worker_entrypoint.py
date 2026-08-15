from __future__ import annotations

import io
import json

from local_llm_server.worker_entrypoint import WorkerSession, run_worker
from local_llm_server.worker_protocol import WorkerState


class _Engine:
    backend = "fake_batch"

    def __init__(self):
        self.closed = False
        self.calls = 0

    def complete(self, payload):
        self.calls += 1
        return {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1},
        }

    def close(self):
        self.closed = True


def test_worker_session_start_prepare_generate_health_stop():
    engine = _Engine()
    captured_cfg = []
    session = WorkerSession(engine_loader=lambda cfg: captured_cfg.append(cfg) or engine)

    start, stop = session.handle({"request_id": "1", "command": "start", "payload": {}})
    assert start["accepted"] is True
    assert start["state"] == "ready"
    assert stop is False

    prepared, _ = session.handle(
        {
            "request_id": "2",
            "command": "prepare",
            "payload": {"config": {"backend": "fake", "model_path": "/private/model"}},
        }
    )
    assert prepared["accepted"] is True
    assert prepared["details"]["prepared"] is True
    assert captured_cfg[0]["worker_isolation"] is False

    generated, _ = session.handle(
        {
            "request_id": "3",
            "command": "generate",
            "payload": {"request": {"messages": [{"role": "user", "content": "hi"}]}, "stream": False},
        }
    )
    assert generated["accepted"] is True
    assert generated["details"]["result"]["usage"]["completion_tokens"] == 1
    assert engine.calls == 1

    health, _ = session.handle({"request_id": "4", "command": "health", "payload": {}})
    assert health["accepted"] is True
    assert health["details"] == {"prepared": True, "backend": "fake_batch"}

    stopped, should_stop = session.handle({"request_id": "5", "command": "stop", "payload": {}})
    assert stopped["accepted"] is True
    assert stopped["state"] == "stopped"
    assert should_stop is True
    assert engine.closed is True
    assert session.state is WorkerState.STOPPED


def test_worker_rejects_streaming_and_cancel_without_faking_support():
    session = WorkerSession(engine_loader=lambda cfg: _Engine())
    session.handle({"request_id": "1", "command": "start", "payload": {}})
    session.handle(
        {
            "request_id": "2",
            "command": "prepare",
            "payload": {"config": {"backend": "fake"}},
        }
    )

    streaming, _ = session.handle(
        {
            "request_id": "3",
            "command": "generate",
            "payload": {"request": {}, "stream": True},
        }
    )
    cancelled, _ = session.handle(
        {"request_id": "4", "command": "cancel", "payload": {}}
    )

    assert streaming["accepted"] is False
    assert streaming["error_code"] == "streaming_not_supported"
    assert cancelled["accepted"] is False
    assert cancelled["error_code"] == "cancel_not_supported"


def test_prepare_failure_is_bounded_and_does_not_expose_exception_text():
    def fail_loader(cfg):
        raise RuntimeError("/private/path secret backend detail")

    session = WorkerSession(engine_loader=fail_loader)
    session.handle({"request_id": "1", "command": "start", "payload": {}})
    response, _ = session.handle(
        {
            "request_id": "2",
            "command": "prepare",
            "payload": {"config": {"backend": "fake"}},
        }
    )

    assert response["accepted"] is False
    assert response["error_code"] == "prepare_failed"
    assert "/private/path" not in str(response)
    assert session.state is WorkerState.READY


def test_run_worker_json_line_protocol_is_deterministic():
    engine = _Engine()
    session = WorkerSession(engine_loader=lambda cfg: engine)
    stdin = io.StringIO(
        "\n".join(
            [
                json.dumps({"request_id": "1", "command": "start", "payload": {}}),
                json.dumps(
                    {
                        "request_id": "2",
                        "command": "prepare",
                        "payload": {"config": {"backend": "fake"}},
                    }
                ),
                json.dumps({"request_id": "3", "command": "stop", "payload": {}}),
            ]
        )
        + "\n"
    )
    stdout = io.StringIO()

    assert run_worker(stdin, stdout, session=session) == 0
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [line["request_id"] for line in lines] == ["1", "2", "3"]
    assert lines[-1]["state"] == "stopped"
