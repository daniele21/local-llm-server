from __future__ import annotations

from fastapi.testclient import TestClient

from local_llm_server.request_middleware import install_request_policy
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.server import create_app


class _Engine:
    backend = "fake"

    def __init__(self):
        self.complete_calls = 0

    def complete(self, payload):
        self.complete_calls += 1
        return {
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }

    def close(self):
        pass


def _app(*, allow_remote_media: bool = False):
    engine = _Engine()
    cfg = {
        "model": "vision",
        "model_id": "org/vision",
        "model_path": "/vision",
        "backend": "fake",
        "host": "127.0.0.1",
        "port": 1235,
        "modalities": ["text", "image"],
        "allow_remote_media": allow_remote_media,
        "default_temperature": 0.0,
        "default_top_p": 1.0,
        "default_top_k": 40,
        "default_min_p": 0.0,
        "default_repeat_penalty": 1.0,
        "thinking_mode": "none",
        "enable_thinking": False,
        "show_thinking": False,
        "force_json": False,
    }
    manager = ModelRuntimeManager(default_model="vision")
    manager.add(cfg, engine)
    application = create_app(manager)
    install_request_policy(application)
    return application, engine


def _remote_image_payload():
    return {
        "model": "vision",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.invalid/private.png"},
                    },
                ],
            }
        ],
        "stream": False,
    }


def test_remote_media_is_rejected_before_backend_by_default():
    application, engine = _app(allow_remote_media=False)

    response = TestClient(application).post(
        "/v1/chat/completions",
        json=_remote_image_payload(),
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_request"
    assert detail["details"]["policy"] == "remote_media_disabled"
    assert engine.complete_calls == 0


def test_remote_media_explicit_opt_in_preserves_compatible_route():
    application, engine = _app(allow_remote_media=True)

    response = TestClient(application).post(
        "/v1/chat/completions",
        json=_remote_image_payload(),
    )

    assert response.status_code == 200
    assert response.json()["content"] == "ok"
    assert engine.complete_calls == 1


def test_text_request_still_reaches_backend_and_policy_install_is_idempotent():
    application, engine = _app()
    install_request_policy(application)

    response = TestClient(application).post(
        "/v1/chat/completions",
        json={
            "model": "vision",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert engine.complete_calls == 1
    assert application.state.canonical_request_policy_installed is True
