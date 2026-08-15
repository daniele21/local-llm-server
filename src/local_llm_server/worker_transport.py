"""Concrete subprocess transport for the worker lifecycle protocol.

This transport owns a child process and exchanges one JSON object per line over
stdin/stdout. It provides bounded round trips and shutdown semantics, but it
does not claim that process exit proves host memory reclamation; B3 evidence
must still compare resource snapshots before/after stop on representative hosts.
"""
from __future__ import annotations

import json
import queue
import subprocess
import threading
import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Callable

from .worker_protocol import (
    WorkerCommand,
    WorkerLifecycle,
    WorkerRequest,
    WorkerResponse,
    WorkerState,
)


ProcessFactory = Callable[..., subprocess.Popen[str]]


class SubprocessWorkerTransport:
    def __init__(
        self,
        command: Sequence[str],
        *,
        env: Mapping[str, str] | None = None,
        process_factory: ProcessFactory = subprocess.Popen,
    ) -> None:
        if not command:
            raise ValueError("worker command must be non-empty")
        self.command = tuple(command)
        self.env = dict(env) if env is not None else None
        self.process_factory = process_factory
        self.lifecycle = WorkerLifecycle()
        self.process: subprocess.Popen[str] | None = None
        self._io_lock = threading.Lock()

    @property
    def state(self) -> WorkerState:
        return self.lifecycle.state

    def start(self, *, timeout: float = 10.0) -> WorkerResponse:
        if not self.lifecycle.accepts(WorkerCommand.START):
            raise RuntimeError(f"worker cannot start from state {self.state.value}")
        self.lifecycle.transition(WorkerState.STARTING)
        try:
            self.process = self.process_factory(
                list(self.command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=self.env,
                start_new_session=True,
            )
            response = self._exchange(
                WorkerRequest(self._request_id(), WorkerCommand.START),
                timeout=timeout,
            )
            if not response.accepted or response.state is not WorkerState.READY:
                raise RuntimeError(response.error_code or "worker rejected startup")
            self.lifecycle.transition(WorkerState.READY)
            return response
        except Exception:
            self._mark_failed()
            self._terminate_process(timeout=min(timeout, 2.0))
            raise

    def request(
        self,
        command: WorkerCommand,
        payload: Mapping[str, Any] | None = None,
        *,
        timeout: float = 30.0,
    ) -> WorkerResponse:
        if command in {WorkerCommand.START, WorkerCommand.STOP}:
            raise ValueError("use start()/stop() for lifecycle commands")
        if not self.lifecycle.accepts(command):
            raise RuntimeError(
                f"worker command {command.value} is not accepted in state {self.state.value}"
            )
        response = self._exchange(
            WorkerRequest(self._request_id(), command, payload or {}),
            timeout=timeout,
        )
        if not response.accepted:
            return response
        if command is WorkerCommand.DRAIN and response.state is WorkerState.DRAINING:
            self.lifecycle.transition(WorkerState.DRAINING)
        elif command is WorkerCommand.CANCEL and self.state is WorkerState.DRAINING and response.state is WorkerState.READY:
            self.lifecycle.transition(WorkerState.READY)
        return response

    def stop(self, *, timeout: float = 5.0) -> None:
        if self.state is WorkerState.STOPPED:
            return
        process = self.process
        if process is None:
            if self.state is WorkerState.NEW:
                self.lifecycle.transition(WorkerState.STOPPED)
            elif self.state is WorkerState.FAILED:
                self.lifecycle.transition(WorkerState.STOPPED)
            return

        previous = self.state
        if previous is not WorkerState.STOPPING:
            try:
                self.lifecycle.transition(WorkerState.STOPPING)
            except ValueError:
                self._mark_failed()
                self.lifecycle.transition(WorkerState.STOPPING)
        try:
            if process.poll() is None and previous not in {WorkerState.NEW, WorkerState.STOPPED}:
                request = WorkerRequest(self._request_id(), WorkerCommand.STOP)
                try:
                    self._exchange(request, timeout=min(timeout, 2.0))
                except Exception:
                    pass
        finally:
            self._terminate_process(timeout=timeout)
            if self.state is WorkerState.STOPPING:
                self.lifecycle.transition(WorkerState.STOPPED)
            elif self.state is WorkerState.FAILED:
                self.lifecycle.transition(WorkerState.STOPPED)

    def close(self, *, timeout: float = 5.0) -> None:
        self.stop(timeout=timeout)

    def _exchange(self, request: WorkerRequest, *, timeout: float) -> WorkerResponse:
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        process = self.process
        if process is None or process.stdin is None or process.stdout is None:
            raise RuntimeError("worker process is not available")
        if process.poll() is not None:
            self._mark_failed()
            raise RuntimeError(f"worker exited with code {process.returncode}")

        with self._io_lock:
            payload = {
                "request_id": request.request_id,
                "command": request.command.value,
                "payload": dict(request.payload),
            }
            process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            process.stdin.flush()

            result_queue: queue.Queue[object] = queue.Queue(maxsize=1)

            def read_one() -> None:
                try:
                    line = process.stdout.readline()
                    result_queue.put(line)
                except Exception as exc:  # pragma: no cover - defensive I/O boundary
                    result_queue.put(exc)

            reader = threading.Thread(target=read_one, daemon=True)
            reader.start()
            try:
                result = result_queue.get(timeout=timeout)
            except queue.Empty as exc:
                self._mark_failed()
                raise TimeoutError(
                    f"worker command {request.command.value} timed out after {timeout:.2f}s"
                ) from exc

            if isinstance(result, Exception):
                self._mark_failed()
                raise RuntimeError(f"worker read failed: {result}") from result
            if not isinstance(result, str) or not result:
                self._mark_failed()
                raise RuntimeError("worker closed stdout without a response")

            try:
                decoded = json.loads(result)
                response = WorkerResponse(
                    request_id=str(decoded["request_id"]),
                    accepted=bool(decoded["accepted"]),
                    state=WorkerState(str(decoded["state"])),
                    error_code=(
                        str(decoded["error_code"])
                        if decoded.get("error_code") is not None
                        else None
                    ),
                    details=(
                        decoded.get("details")
                        if isinstance(decoded.get("details"), Mapping)
                        else {}
                    ),
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                self._mark_failed()
                raise RuntimeError("worker returned an invalid response envelope") from exc

            if response.request_id != request.request_id:
                self._mark_failed()
                raise RuntimeError("worker response request_id does not match request")
            return response

    def _terminate_process(self, *, timeout: float) -> None:
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=max(timeout, 0.1))
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=max(timeout, 0.1))
        self.process = None

    def _mark_failed(self) -> None:
        if self.state in {WorkerState.STOPPED, WorkerState.FAILED}:
            return
        try:
            self.lifecycle.transition(WorkerState.FAILED)
        except ValueError:
            pass

    @staticmethod
    def _request_id() -> str:
        return uuid.uuid4().hex
