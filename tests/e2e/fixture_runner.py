#!/usr/bin/env python3
"""Own the deterministic E2E server process and its run-scoped temporary state."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from lifecycle import OwnedRunState, listener_open

HOST = "127.0.0.1"
PORT = 8765
CHILD_SHUTDOWN_SECONDS = 3.5
POST_STOP_VERIFY_SECONDS = 1.0


class FixtureRunner:
    def __init__(self) -> None:
        self.run_state = OwnedRunState.create()
        self.child: subprocess.Popen[str] | None = None
        self.stop_requested = False

    def _signal_handler(self, signum: int, _frame) -> None:
        self.stop_requested = True
        child = self.child
        if child is None or child.poll() is not None:
            return
        forwarded = signal.SIGINT if signum == signal.SIGINT else signal.SIGTERM
        try:
            child.send_signal(forwarded)
        except ProcessLookupError:
            pass

    def _start_child(self) -> subprocess.Popen[str]:
        env = os.environ.copy()
        env["LOCAL_LLM_E2E_RUN_ID"] = self.run_state.run_id
        env["LOCAL_LLM_E2E_ROOT"] = str(self.run_state.root)
        return subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("fixture_server.py"))],
            env=env,
            text=True,
        )

    def _stop_child(self) -> None:
        child = self.child
        if child is None or child.poll() is not None:
            return
        try:
            child.send_signal(signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            child.wait(timeout=CHILD_SHUTDOWN_SECONDS)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=1.0)

    def _cleanup_owned_state(self) -> None:
        if self.run_state.root.exists():
            self.run_state.cleanup()

    def _verify_stopped(self) -> None:
        deadline = time.monotonic() + POST_STOP_VERIFY_SECONDS
        while True:
            root_exists = self.run_state.root.exists()
            listener = listener_open(HOST, PORT)
            if not root_exists and not listener:
                return
            if time.monotonic() >= deadline:
                problems: list[str] = []
                if root_exists:
                    problems.append(f"owned temp root remains: {self.run_state.root}")
                if listener:
                    problems.append(f"listener remains open on {HOST}:{PORT}")
                raise RuntimeError("; ".join(problems))
            time.sleep(0.05)

    def run(self) -> int:
        previous_term = signal.signal(signal.SIGTERM, self._signal_handler)
        previous_int = signal.signal(signal.SIGINT, self._signal_handler)
        try:
            self.child = self._start_child()
            while True:
                return_code = self.child.poll()
                if return_code is not None:
                    return return_code
                if self.stop_requested:
                    try:
                        return self.child.wait(timeout=CHILD_SHUTDOWN_SECONDS)
                    except subprocess.TimeoutExpired:
                        self.child.kill()
                        return self.child.wait(timeout=1.0)
                time.sleep(0.05)
        finally:
            try:
                self._stop_child()
            finally:
                self._cleanup_owned_state()
                self._verify_stopped()
                signal.signal(signal.SIGTERM, previous_term)
                signal.signal(signal.SIGINT, previous_int)


def main() -> int:
    return FixtureRunner().run()


if __name__ == "__main__":
    raise SystemExit(main())
