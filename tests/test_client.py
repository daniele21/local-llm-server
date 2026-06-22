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
