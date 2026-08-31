from __future__ import annotations

import subprocess
from pathlib import Path

from local_llm_server.llama_server_compat import (
    LlamaServerBuildIdentity,
    probe_llama_server_version,
    validate_llama_server_binary,
)


def _make_executable(path: Path) -> Path:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_default_probe_reuses_positive_identity_for_unchanged_binary(monkeypatch, tmp_path):
    binary = _make_executable(tmp_path / "llama-server")
    calls: list[Path] = []

    def runner(path: Path) -> str:
        calls.append(path)
        if len(calls) > 1:
            raise subprocess.TimeoutExpired([str(path), "--version"], timeout=2.0)
        return "version: 10621 (c1d0e7a)\n"

    monkeypatch.setattr("local_llm_server.llama_server_compat._default_runner", runner)

    first = validate_llama_server_binary(binary)
    second = validate_llama_server_binary(binary)

    assert first.backend_version == "build-10621@c1d0e7a"
    assert second == first
    assert calls == [binary]


def test_default_probe_revalidates_after_executable_changes(monkeypatch, tmp_path):
    binary = _make_executable(tmp_path / "llama-server")
    outputs = iter((
        "version: 10621 (c1d0e7a)\n",
        "version: 10622 (abcdef1)\n",
    ))
    calls: list[Path] = []

    def runner(path: Path) -> str:
        calls.append(path)
        return next(outputs)

    monkeypatch.setattr("local_llm_server.llama_server_compat._default_runner", runner)

    first = validate_llama_server_binary(binary)
    binary.write_text("#!/bin/sh\n# replaced executable\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)
    second = validate_llama_server_binary(binary)

    assert first.backend_version == "build-10621@c1d0e7a"
    assert second.backend_version == "build-10622@abcdef1"
    assert calls == [binary, binary]


def test_failed_default_probe_is_not_cached(monkeypatch, tmp_path):
    binary = _make_executable(tmp_path / "llama-server")
    calls = 0

    def runner(path: Path) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise subprocess.TimeoutExpired([str(path), "--version"], timeout=2.0)
        return "version: 10621 (c1d0e7a)\n"

    monkeypatch.setattr("local_llm_server.llama_server_compat._default_runner", runner)

    assert probe_llama_server_version(binary) is None
    identity = probe_llama_server_version(binary)

    assert identity == LlamaServerBuildIdentity(build=10621, commit="c1d0e7a")
    assert calls == 2


def test_injected_runner_bypasses_process_cache(monkeypatch, tmp_path):
    binary = _make_executable(tmp_path / "llama-server")
    default_calls = 0

    def default_runner(_path: Path) -> str:
        nonlocal default_calls
        default_calls += 1
        return "version: 10621 (c1d0e7a)\n"

    monkeypatch.setattr("local_llm_server.llama_server_compat._default_runner", default_runner)
    assert probe_llama_server_version(binary) == LlamaServerBuildIdentity(
        build=10621,
        commit="c1d0e7a",
    )

    injected_calls = 0

    def injected_runner(_path: Path) -> str:
        nonlocal injected_calls
        injected_calls += 1
        return "version: 10699 (abcdef1)\n"

    identity = probe_llama_server_version(binary, run_command=injected_runner)

    assert identity == LlamaServerBuildIdentity(build=10699, commit="abcdef1")
    assert default_calls == 1
    assert injected_calls == 1
