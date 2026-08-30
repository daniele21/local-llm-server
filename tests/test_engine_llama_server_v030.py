from __future__ import annotations

from pathlib import Path

import pytest

from local_llm_server.engine import LlamaServerEngine
from local_llm_server.llama_server_compat import (
    LlamaServerBuildIdentity,
    LlamaServerCompatibility,
)


class _FakeProcess:
    instances = []
    fail_ready = False

    def __init__(self, cmd, *, name, logger, env=None):
        self.cmd = list(cmd)
        self.name = name
        self.started = False
        self.closed = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True

    def wait_ready(self, predicate, *, timeout):
        if self.__class__.fail_ready:
            raise RuntimeError("readiness failed")

    def close(self):
        self.closed = True


def _cfg(tmp_path: Path) -> dict:
    return {
        "model": "demo",
        "model_id": "org/demo",
        "backend": "llama_server",
        "model_path": str(tmp_path / "model.gguf"),
        "download_url": "",
        "no_download": True,
        "ctx_size": 16384,
        "n_threads": 6,
        "n_batch": 1024,
        "n_ubatch": 256,
        "flash_attn": True,
        "max_concurrent_requests": 2,
        "llama_server_port": 8091,
        "llama_server_cont_batching": True,
        "llama_server_kv_unified": True,
        "llama_server_gpu_layers": "auto",
        "llama_server_load_mode": "auto",
        "llama_server_fit": True,
        "startup_timeout": 30,
    }


def _compatibility() -> LlamaServerCompatibility:
    return LlamaServerCompatibility(
        identity=LlamaServerBuildIdentity(build=10621, commit="c1d0e7a"),
        supported=True,
    )


def _patch_dependencies(monkeypatch, tmp_path):
    binary = tmp_path / "llama-server"
    monkeypatch.setattr("local_llm_server.engine.ensure_model", lambda **_kwargs: None)
    monkeypatch.setattr(
        "local_llm_server.engine.resolve_llama_server_binary",
        lambda _cfg: (binary, _compatibility()),
    )
    monkeypatch.setattr("local_llm_server.engine.ManagedProcess", _FakeProcess)
    _FakeProcess.instances.clear()
    _FakeProcess.fail_ready = False
    return binary


def test_engine_wires_validated_build_identity_and_parallel_server_slots(monkeypatch, tmp_path):
    binary = _patch_dependencies(monkeypatch, tmp_path)

    engine = LlamaServerEngine(_cfg(tmp_path))

    [process] = _FakeProcess.instances
    assert process.started is True
    assert process.cmd[0] == str(binary)
    assert process.cmd[process.cmd.index("--parallel") + 1] == "2"
    assert "--cont-batching" in process.cmd
    assert "--kv-unified" in process.cmd
    assert process.cmd[process.cmd.index("--load-mode") + 1] == "auto"
    assert process.cmd[process.cmd.index("--fit") + 1] == "on"
    assert engine.backend_version == "build-10621@c1d0e7a"
    assert engine.backend_compatibility_profile == "validated-v0.3.0"

    engine.close()
    engine.close()

    assert process.closed is True
    assert engine.process is None


def test_partial_startup_failure_closes_owned_subprocess(monkeypatch, tmp_path):
    _patch_dependencies(monkeypatch, tmp_path)
    _FakeProcess.fail_ready = True

    with pytest.raises(RuntimeError, match="readiness failed"):
        LlamaServerEngine(_cfg(tmp_path))

    [process] = _FakeProcess.instances
    assert process.started is True
    assert process.closed is True
