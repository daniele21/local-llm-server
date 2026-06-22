from __future__ import annotations

import json
from pathlib import Path

from local_llm_server.engine import LlamaServerEngine, load_llm


class _HealthResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return b'{"status":"ok"}'


class _CompletionResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode("utf-8")


class _Process:
    stdout = None

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0


def test_load_llm_supports_llama_server(monkeypatch, tmp_path):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model")
    binary = tmp_path / "llama-server"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    monkeypatch.setattr("local_llm_server.engine.ensure_model", lambda **_kwargs: None)
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: _Process())
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=0: _HealthResponse()
        if str(getattr(request, "full_url", request)).endswith("/health")
        else _CompletionResponse(),
    )

    engine = load_llm(
        {
            "backend": "llama_server",
            "model_path": str(model),
            "llama_server_bin": str(binary),
            "llama_server_port": 19091,
            "ctx_size": 4096,
            "startup_timeout": 1,
            "timeout": 5,
            "download_url": "",
            "no_download": True,
        }
    )

    assert isinstance(engine, LlamaServerEngine)
    assert engine.create_chat_completion(messages=[], stream=False)["choices"][0]["message"]["content"] == "ok"
    engine.shutdown()


def test_resolve_binary_prefers_explicit(tmp_path):
    binary = tmp_path / "llama-server"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    assert LlamaServerEngine._resolve_binary({"llama_server_bin": str(binary)}) == Path(binary)
