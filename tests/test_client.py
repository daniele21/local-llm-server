from __future__ import annotations

import json

from local_llm_server.client import LocalLLMClient


class _Response:
    status = 200

    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_analyze_text_parses_json(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url.endswith("/v1/chat/completions")
        return _Response({"choices": [{"message": {"content": '{"title":"T","summary":"S","key_points":[],"action_items":[]}'}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = LocalLLMClient()
    result = client.analyze_text("testo")

    assert result == {"title": "T", "summary": "S", "key_points": [], "action_items": []}


def test_chat_prefers_server_output(monkeypatch):
    def fake_urlopen(request, timeout):
        return _Response({"output": "ciao"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert LocalLLMClient().chat([{"role": "user", "content": "ciao"}]) == "ciao"


def test_analyze_image_sends_multimodal_message(monkeypatch, tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["messages"][0]["content"][0]["type"] == "image_url"
        assert payload["temperature"] == 0.0
        assert payload["max_tokens"] == 512
        return _Response({"choices": [{"message": {"content": "un'immagine"}}]})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert LocalLLMClient().analyze_image(image) == "un'immagine"
