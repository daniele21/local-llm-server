"""Small, reusable lifecycle wrapper for backend subprocesses."""
from __future__ import annotations

import collections
import logging
import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Mapping, Sequence


class ManagedProcess:
    def __init__(
        self,
        command: Sequence[str],
        *,
        name: str,
        logger: logging.Logger,
        env: Mapping[str, str] | None = None,
        tail_lines: int = 200,
    ) -> None:
        self.command = list(command)
        self.name = name
        self.logger = logger
        self.env = dict(env) if env is not None else None
        self._tail: collections.deque[str] = collections.deque(maxlen=tail_lines)
        self._tail_lock = threading.Lock()
        self.process: subprocess.Popen[str] | None = None
        self._log_thread: threading.Thread | None = None

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError(f"{self.name} is already running.")
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=self.env,
            start_new_session=True,
        )
        self._log_thread = threading.Thread(
            target=self._drain_logs,
            name=f"{self.name}-logs",
            daemon=True,
        )
        self._log_thread.start()

    def _drain_logs(self) -> None:
        process = self.process
        if process is None or process.stdout is None:
            return
        try:
            for line in process.stdout:
                cleaned = line.rstrip("\r\n")
                with self._tail_lock:
                    self._tail.append(cleaned)
                self.logger.info("[%s] %s", self.name, cleaned)
        except (OSError, ValueError):
            self.logger.debug("Log stream for %s closed.", self.name)

    def wait_ready(
        self,
        check_ready: Callable[[], bool],
        *,
        timeout: float,
        interval: float = 1.0,
    ) -> None:
        deadline = time.monotonic() + timeout
        last_error = ""
        while time.monotonic() < deadline:
            process = self.process
            if process is None:
                raise RuntimeError(f"{self.name} has not been started.")
            return_code = process.poll()
            if return_code is not None:
                self._join_log_thread()
                tail = "\n".join(self.tail_logs())
                raise RuntimeError(
                    f"{self.name} exited during startup with code {return_code}. {tail}"
                )
            try:
                if check_ready():
                    return
            except Exception as exc:
                last_error = str(exc)
            time.sleep(interval)
        self.close()
        raise TimeoutError(
            f"{self.name} did not become ready within {timeout:.0f}s. "
            f"Last error: {last_error or 'not ready'}"
        )

    def tail_logs(self) -> list[str]:
        with self._tail_lock:
            return list(self._tail)

    def close(self, *, timeout: float = 5.0) -> None:
        process = self.process
        if process is None:
            return
        if process.poll() is None:
            self.logger.info("Stopping %s", self.name)
            self._signal_process_group(process, signal.SIGTERM)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._signal_process_group(process, signal.SIGKILL)
                process.wait(timeout=timeout)
        self._join_log_thread(timeout=timeout)
        self.process = None

    @staticmethod
    def _signal_process_group(process: subprocess.Popen[str], signum: int) -> None:
        """Signal the subprocess session, with a portable process fallback."""
        if os.name == "posix" and getattr(process, "pid", None):
            try:
                os.killpg(os.getpgid(process.pid), signum)
                return
            except (OSError, ProcessLookupError):
                pass
        if signum == signal.SIGKILL:
            process.kill()
        else:
            process.terminate()

    def _join_log_thread(self, *, timeout: float = 0.2) -> None:
        thread = self._log_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)
