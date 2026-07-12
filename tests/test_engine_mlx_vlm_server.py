from __future__ import annotations

import json
import io
import urllib.error

import pytest

from local_llm_server.engine import MLXVLMServerEngine, load_llm


class _HealthResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return b'{"status":"healthy"}'


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


def test_mlx_vlm_server_uses_local_model_and_openai_endpoint(monkeypatch, tmp_path):
    model = tmp_path / "Qwen3-VL-4B-Instruct-MLX-4bit"
    model.mkdir()
    commands = []

    monkeypatch.setattr("subprocess.Popen", lambda command, **_kwargs: commands.append(command) or _Process())
    requests = []

    def urlopen(request, timeout=0):
        if str(getattr(request, "full_url", request)).endswith("/health"):
            return _HealthResponse()
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
        }
    )

    assert isinstance(engine, MLXVLMServerEngine)
    assert commands[0][1:4] == ["-m", "mlx_vlm.server", "--model"]
    assert commands[0][4] == str(model)
    assert engine.create_chat_completion(messages=[], stream=False)["choices"][0]["message"]["content"] == "ok"
    assert requests[0]["model"] == str(model)
    engine.shutdown()


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
        engine.create_chat_completion(messages=[], stream=False)
