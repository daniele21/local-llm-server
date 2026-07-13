from __future__ import annotations

import logging
import subprocess

import pytest

from local_llm_server.process import ManagedProcess


class _Process:
    def __init__(self, *, return_code=None, lines=()):
        self.return_code = return_code
        self.stdout = iter(lines)
        self.terminated = False
        self.killed = False
        self.pid = None

    def poll(self):
        return self.return_code

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True

    def wait(self, timeout=None):
        self.return_code = 0
        return 0


def test_managed_process_starts_log_drain_and_keeps_tail(monkeypatch):
    fake = _Process(lines=("one\n", "two\n"))
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: fake)
    process = ManagedProcess(["fake"], name="fake", logger=logging.getLogger("test"))

    process.start()
    process._log_thread.join(timeout=1)

    assert process.tail_logs() == ["one", "two"]


def test_managed_process_reports_tail_when_startup_exits(monkeypatch):
    fake = _Process(return_code=2, lines=("fatal\n",))
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: fake)
    process = ManagedProcess(["fake"], name="fake", logger=logging.getLogger("test"))
    process.start()
    process._log_thread.join(timeout=1)

    with pytest.raises(RuntimeError, match="fatal"):
        process.wait_ready(lambda: False, timeout=1, interval=0)


def test_managed_process_kills_after_terminate_timeout(monkeypatch):
    fake = _Process()

    def wait(timeout=None):
        if not fake.killed:
            raise subprocess.TimeoutExpired("fake", timeout)
        return 0

    fake.wait = wait
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: fake)
    process = ManagedProcess(["fake"], name="fake", logger=logging.getLogger("test"))
    process.start()
    process.close(timeout=0.01)

    assert fake.terminated is True
    assert fake.killed is True


def test_managed_process_signals_the_process_group_on_posix(monkeypatch):
    fake = _Process()
    fake.pid = 1234
    signals = []
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: fake)
    monkeypatch.setattr("os.getpgid", lambda pid: pid)
    monkeypatch.setattr("os.killpg", lambda pgid, signum: signals.append((pgid, signum)))
    process = ManagedProcess(["fake"], name="fake", logger=logging.getLogger("test"))
    process.start()
    process.close()

    assert signals
    assert signals[0][0] == 1234
