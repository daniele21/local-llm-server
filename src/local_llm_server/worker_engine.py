"""Engine adapter backed by the isolated JSON-line worker process.

This first adoption slice is deliberately batch/non-streaming. It is suitable for
completed-response evaluation and lifecycle evidence without pretending buffered
chunks are true streaming output.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .worker_protocol import WorkerCommand
from .worker_transport import SubprocessWorkerTransport


TransportFactory = Callable[..., SubprocessWorkerTransport]


class WorkerBackedEngine:
    execution_isolation = "subprocess_worker"
    supports_streaming = False

    def __init__(
        self,
        cfg: Mapping[str, Any],
        *,
        transport_factory: TransportFactory = SubprocessWorkerTransport,
        startup_timeout: float | None = None,
    ) -> None:
        self.cfg = dict(cfg)
        self.backend = str(self.cfg.get("backend") or "unknown")
        command = [sys.executable, "-m", "local_llm_server.worker_entrypoint"]
        self.transport = transport_factory(
            command,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        timeout = float(
            startup_timeout
            if startup_timeout is not None
            else self.cfg.get("startup_timeout") or 60.0
        )
        self.transport.start(timeout=timeout)
        prepared = self.transport.request(
            WorkerCommand.PREPARE,
            {"config": _json_safe(self.cfg)},
            timeout=timeout,
        )
        if not prepared.accepted:
            self.transport.stop(timeout=min(timeout, 5.0))
            raise RuntimeError(prepared.error_code or "worker preparation failed")

    def complete(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.transport.request(
            WorkerCommand.GENERATE,
            {"request": _json_safe(payload), "stream": False},
            timeout=float(self.cfg.get("timeout") or 1200.0),
        )
        if not response.accepted:
            raise RuntimeError(response.error_code or "worker generation failed")
        result = response.details.get("result")
        if not isinstance(result, Mapping):
            raise RuntimeError("worker returned an invalid completion result")
        return dict(result)

    def stream(self, payload: dict[str, Any]):
        raise RuntimeError(
            "worker-backed streaming is not supported by the current incremental protocol"
        )

    def health(self) -> dict[str, Any]:
        response = self.transport.request(WorkerCommand.HEALTH, timeout=5.0)
        return {
            "accepted": response.accepted,
            "state": response.state.value,
            "prepared": bool(response.details.get("prepared")),
            "backend": response.details.get("backend"),
        }

    def close(self) -> None:
        self.transport.stop(timeout=5.0)

    shutdown = close


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    return str(value)
