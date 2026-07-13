from __future__ import annotations

import json
import io
import urllib.error

import pytest

from local_llm_server.engine import MLXVLMServerEngine, load_llm


class _HealthResponse:
    status = 200

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps({"status": "healthy", "loaded_model": self.model_path}).encode()


class _CompletionResponse(_HealthResponse):
    def read(self):
        return json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()


class _Process:
    stdout = None

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0


def _write_complete_vlm(path):
    path.mkdir()
    (path / "config.json").write_text("{}")
    (path / "tokenizer_config.json").write_text("{}")
    (path / "preprocessor_config.json").write_text("{}")
    (path / "model.safetensors").write_bytes(b"weights")


def test_mlx_vlm_server_uses_local_model_and_openai_endpoint(monkeypatch, tmp_path):
    model = tmp_path / "Qwen3-VL-4B-Instruct-MLX-4bit"
    _write_complete_vlm(model)
    commands = []

    monkeypatch.setattr("subprocess.Popen", lambda command, **_kwargs: commands.append(command) or _Process())
    requests = []

    def urlopen(request, timeout=0):
        if str(getattr(request, "full_url", request)).endswith("/health"):
            return _HealthResponse(str(model))
        requests.append(json.loads(request.data.decode("utf-8")))
        return _CompletionResponse()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)

    engine = load_llm(
        {
            "backend": "mlx_vlm_server",
            "model_path": str(model),
            "mlx_vlm_server_port": 19092,
            "startup_timeout": 1,
            "timeout": 5,
            "max_kv_size": 8192,
            "thinking_mode": "none",
        }
    )

    assert isinstance(engine, MLXVLMServerEngine)
    assert commands[0][1:4] == ["-m", "mlx_vlm.server", "--model"]
    assert commands[0][4] == str(model)
    assert commands[0][-2:] == ["--max-kv-size", "8192"]
    assert engine.complete({"messages": [], "repeat_penalty": 1.2})["choices"][0]["message"]["content"] == "ok"
    assert requests[0]["model"] == str(model)
    assert requests[0]["repetition_penalty"] == 1.2
    assert "repeat_penalty" not in requests[0]
    assert "enable_thinking" not in requests[0]
    engine.close()


def test_mlx_vlm_switchable_thinking_is_forwarded(monkeypatch):
    engine = object.__new__(MLXVLMServerEngine)
    engine.base_url = "http://127.0.0.1:19092"
    engine.model_path = "/models/qwen-vl-thinking"
    engine.cfg = {"timeout": 5, "thinking_mode": "switchable"}
    requests = []

    def urlopen(request, timeout=0):
        requests.append(json.loads(request.data.decode("utf-8")))
        return _CompletionResponse()

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    engine.complete({"messages": [], "enable_thinking": False})

    assert requests[0]["enable_thinking"] is False


def test_mlx_vlm_server_exposes_backend_http_error(monkeypatch):
    engine = object.__new__(MLXVLMServerEngine)
    engine.base_url = "http://127.0.0.1:19092"
    engine.model_path = "/models/qwen-vl"
    engine.cfg = {"timeout": 5}

    def fail(*_args, **_kwargs):
        raise urllib.error.HTTPError(
            engine.base_url, 400, "Bad Request", {}, io.BytesIO(b'{"detail":"invalid image"}')
        )

    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(RuntimeError, match="invalid image"):
        engine.complete({"messages": []})


def test_mlx_vlm_readiness_rejects_the_wrong_loaded_model(monkeypatch):
    engine = object.__new__(MLXVLMServerEngine)
    engine.base_url = "http://127.0.0.1:19092"
    engine.model_path = "/models/expected"
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *_args, **_kwargs: _HealthResponse("/models/unexpected"),
    )

    with pytest.raises(RuntimeError, match="unexpected model"):
        engine._is_ready()
