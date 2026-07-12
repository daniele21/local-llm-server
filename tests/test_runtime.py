from __future__ import annotations

import threading

import pytest

from local_llm_server.runtime import ModelRuntimeManager, config_capabilities_for_backend


class _Engine:
    def __init__(self, backend="fake"):
        self.backend = backend
        self.stopped = False

    def shutdown(self):
        self.stopped = True


def _cfg(key, *, backend="fake", model_id=None, port=None):
    cfg = {"model": key, "model_id": model_id or key, "backend": backend}
    if backend == "llama_server":
        cfg["llama_server_port"] = port or 8091
    return cfg


def test_manager_routes_by_key_and_model_id():
    manager = ModelRuntimeManager(default_model="text")
    runtime = manager.add(_cfg("text", model_id="org/text"), _Engine())

    assert manager.resolve() is runtime
    assert manager.resolve("text") is runtime
    assert manager.resolve("org/text") is runtime


def test_manager_keeps_multiple_models_loaded_and_shutdowns_all():
    manager = ModelRuntimeManager()
    first = manager.add(_cfg("first"), _Engine())
    second = manager.add(_cfg("second"), _Engine())

    manager.shutdown()

    assert first.engine.stopped is True
    assert second.engine.stopped is True
    assert manager.list() == []


def test_manager_does_not_unload_last_model():
    manager = ModelRuntimeManager()
    manager.add(_cfg("only"), _Engine())

    with pytest.raises(RuntimeError, match="last resident"):
        manager.unload("only")


def test_manager_rejects_unload_while_model_is_busy():
    manager = ModelRuntimeManager()
    runtime = manager.add(_cfg("busy"), _Engine())
    manager.add(_cfg("idle"), _Engine())
    acquired = threading.Event()
    release = threading.Event()

    def hold_lock():
        with runtime.lock:
            acquired.set()
            release.wait(timeout=2)

    thread = threading.Thread(target=hold_lock)
    thread.start()
    acquired.wait(timeout=2)
    with pytest.raises(RuntimeError, match="active request"):
        manager.unload("busy")
    release.set()
    thread.join(timeout=2)


def test_private_ports_are_unique(monkeypatch):
    manager = ModelRuntimeManager()
    manager.add(_cfg("one", backend="llama_server", port=8091), _Engine("llama_server"))
    captured = {}

    monkeypatch.setattr("local_llm_server.config.build_config", lambda **_kwargs: _cfg("two", backend="llama_server", port=8091))
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda cfg: captured.update(cfg) or _Engine("llama_server"))

    runtime, loaded = manager.load("two")

    assert loaded is True
    assert runtime.cfg["llama_server_port"] == 8092
    assert captured["llama_server_port"] == 8092


def test_reload_replaces_only_target_runtime(monkeypatch):
    manager = ModelRuntimeManager(default_model="one")
    old_engine = _Engine()
    other_engine = _Engine()
    manager.add(_cfg("one"), old_engine)
    other = manager.add(_cfg("two"), other_engine)
    replacement_engine = _Engine()

    monkeypatch.setattr("local_llm_server.config.build_config", lambda **_kwargs: _cfg("one"))
    monkeypatch.setattr("local_llm_server.engine.load_llm", lambda _cfg: replacement_engine)

    replacement = manager.reload("one", ctx_size=8192)

    assert manager.resolve("one") is replacement
    assert replacement.engine is replacement_engine
    assert manager.resolve("two") is other
    assert old_engine.stopped is True
    assert other_engine.stopped is False


def test_backend_config_capabilities_match_consumed_engine_settings():
    llama_cpp = config_capabilities_for_backend("llama_cpp")
    mlx_vlm = config_capabilities_for_backend("mlx_vlm_server")

    assert "n_gpu_layers" in llama_cpp
    assert "n_batch" in llama_cpp
    assert "n_gpu_layers" not in mlx_vlm
    assert "n_batch" not in mlx_vlm
    assert mlx_vlm == ["timeout"]
