from __future__ import annotations

import json
import sys

import pytest

from local_llm_server.worker_protocol import WorkerCommand, WorkerState
from local_llm_server.worker_transport import SubprocessWorkerTransport


_WORKER_SCRIPT = r'''
import json
import sys
state = "starting"
for line in sys.stdin:
    req = json.loads(line)
    command = req["command"]
    if command == "start":
        state = "ready"
        details = {"pid_owned": True}
    elif command == "generate":
        details = {"echo": req.get("payload", {}).get("text")}
    elif command == "health":
        details = {"healthy": True}
    elif command == "drain":
        state = "draining"
        details = {}
    elif command == "cancel":
        state = "ready"
        details = {}
    elif command == "stop":
        state = "stopped"
        details = {}
    else:
        details = {}
    response = {
        "request_id": req["request_id"],
        "accepted": True,
        "state": state,
        "details": details,
    }
    print(json.dumps(response), flush=True)
    if command == "stop":
        break
'''


def test_subprocess_transport_owns_start_request_and_stop_lifecycle():
    transport = SubprocessWorkerTransport(
        [sys.executable, "-u", "-c", _WORKER_SCRIPT]
    )

    started = transport.start(timeout=3)
    assert started.accepted is True
    assert transport.state is WorkerState.READY
    assert transport.process is not None

    generated = transport.request(
        WorkerCommand.GENERATE,
        {"text": "hello"},
        timeout=3,
    )
    assert generated.details["echo"] == "hello"

    health = transport.request(WorkerCommand.HEALTH, timeout=3)
    assert health.details["healthy"] is True

    drained = transport.request(WorkerCommand.DRAIN, timeout=3)
    assert drained.state is WorkerState.DRAINING
    assert transport.state is WorkerState.DRAINING

    cancelled = transport.request(WorkerCommand.CANCEL, timeout=3)
    assert cancelled.state is WorkerState.READY
    assert transport.state is WorkerState.READY

    transport.stop(timeout=3)
    assert transport.state is WorkerState.STOPPED
    assert transport.process is None


def test_transport_rejects_generation_before_worker_is_ready():
    transport = SubprocessWorkerTransport([sys.executable, "-u", "-c", _WORKER_SCRIPT])
    with pytest.raises(RuntimeError, match="not accepted"):
        transport.request(WorkerCommand.GENERATE, {"text": "x"})
    transport.stop()
    assert transport.state is WorkerState.STOPPED


def test_invalid_response_marks_worker_failed():
    script = "import sys; print('not-json', flush=True); sys.stdin.readline()"
    transport = SubprocessWorkerTransport([sys.executable, "-u", "-c", script])
    with pytest.raises(RuntimeError, match="invalid response"):
        transport.start(timeout=3)
    assert transport.state in {WorkerState.FAILED, WorkerState.STOPPED}


def test_request_id_mismatch_is_rejected():
    script = r'''
import json, sys
req = json.loads(sys.stdin.readline())
print(json.dumps({"request_id":"wrong","accepted":True,"state":"ready"}), flush=True)
'''
    transport = SubprocessWorkerTransport([sys.executable, "-u", "-c", script])
    with pytest.raises(RuntimeError, match="request_id"):
        transport.start(timeout=3)
