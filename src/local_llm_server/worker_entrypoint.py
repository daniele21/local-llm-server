"""JSON-line worker process for isolated non-streaming inference.

The worker receives runtime configuration only over stdin after process start, so
private model paths are not embedded in the command line. It deliberately
supports completed-response generation first; true incremental streaming needs a
separate event protocol and is not emulated by buffering chunks.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from typing import Any, TextIO

from .worker_protocol import WorkerCommand, WorkerState


EngineLoader = Callable[[dict[str, Any]], Any]


class WorkerSession:
    def __init__(self, *, engine_loader: EngineLoader | None = None) -> None:
        self.state = WorkerState.NEW
        self.engine: Any | None = None
        self._engine_loader = engine_loader

    def handle(self, envelope: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        request_id = str(envelope.get("request_id") or "")
        raw_command = envelope.get("command")
        payload = envelope.get("payload")
        payload_map = payload if isinstance(payload, Mapping) else {}
        try:
            command = WorkerCommand(str(raw_command))
        except ValueError:
            return self._response(request_id, False, "invalid_command"), False

        if command is WorkerCommand.START:
            if self.state is not WorkerState.NEW:
                return self._response(request_id, False, "invalid_state"), False
            self.state = WorkerState.READY
            return self._response(request_id, True, details={"prepared": False}), False

        if command is WorkerCommand.HEALTH:
            return self._response(
                request_id,
                self.state is not WorkerState.STOPPED,
                details={
                    "prepared": self.engine is not None,
                    "backend": getattr(self.engine, "backend", None),
                },
            ), False

        if command is WorkerCommand.PREPARE:
            if self.state is not WorkerState.READY or self.engine is not None:
                return self._response(request_id, False, "invalid_state"), False
            config = payload_map.get("config")
            if not isinstance(config, Mapping):
                return self._response(request_id, False, "invalid_config"), False
            cfg = dict(config)
            # Prevent accidental recursive worker wrapping if a future product
            # config gains an isolation toggle.
            cfg["worker_isolation"] = False
            try:
                loader = self._engine_loader
                if loader is None:
                    from .engine import load_llm

                    loader = load_llm
                self.engine = loader(cfg)
            except BaseException:
                self.engine = None
                return self._response(request_id, False, "prepare_failed"), False
            return self._response(
                request_id,
                True,
                details={"prepared": True, "backend": getattr(self.engine, "backend", None)},
            ), False

        if command is WorkerCommand.GENERATE:
            if self.state is not WorkerState.READY or self.engine is None:
                return self._response(request_id, False, "not_prepared"), False
            if payload_map.get("stream") is True:
                return self._response(request_id, False, "streaming_not_supported"), False
            request_payload = payload_map.get("request")
            if not isinstance(request_payload, Mapping):
                return self._response(request_id, False, "invalid_request"), False
            complete = getattr(self.engine, "complete", None)
            if not callable(complete):
                return self._response(request_id, False, "completion_not_supported"), False
            try:
                result = complete(dict(request_payload))
                # Validate the result is safe for the JSON-line transport before
                # we place it into the public response envelope.
                json.dumps(result, separators=(",", ":"))
            except BaseException:
                return self._response(request_id, False, "generation_failed"), False
            return self._response(request_id, True, details={"result": result}), False

        if command is WorkerCommand.DRAIN:
            if self.state is not WorkerState.READY:
                return self._response(request_id, False, "invalid_state"), False
            self.state = WorkerState.DRAINING
            return self._response(request_id, True), False

        if command is WorkerCommand.CANCEL:
            # The first worker slice executes one synchronous completed request
            # at a time. Do not pretend that it can interrupt an in-flight call.
            return self._response(request_id, False, "cancel_not_supported"), False

        if command is WorkerCommand.STOP:
            if self.state is WorkerState.STOPPED:
                return self._response(request_id, True), True
            self.state = WorkerState.STOPPING
            engine = self.engine
            self.engine = None
            if engine is not None:
                close = getattr(engine, "close", None) or getattr(engine, "shutdown", None)
                if callable(close):
                    try:
                        close()
                    except BaseException:
                        pass
            self.state = WorkerState.STOPPED
            return self._response(request_id, True), True

        return self._response(request_id, False, "unsupported_command"), False

    def _response(
        self,
        request_id: str,
        accepted: bool,
        error_code: str | None = None,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "accepted": accepted,
            "state": self.state.value,
            "error_code": error_code,
            "details": dict(details or {}),
        }


def run_worker(
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
    *,
    session: WorkerSession | None = None,
) -> int:
    worker = session or WorkerSession()
    for raw in stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            response = {
                "request_id": "invalid",
                "accepted": False,
                "state": worker.state.value,
                "error_code": "invalid_json",
                "details": {},
            }
            stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            stdout.flush()
            continue
        if not isinstance(envelope, Mapping):
            continue
        response, stop = worker.handle(envelope)
        stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
        stdout.flush()
        if stop:
            break
    return 0


def main() -> int:
    return run_worker()


if __name__ == "__main__":
    raise SystemExit(main())
