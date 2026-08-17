from __future__ import annotations

from local_llm_server.llama_cpp_request import (
    LlamaCppThinkingControlError,
    chat_completion,
)


class _FakeLlama:
    def __init__(self, *, with_metadata_handler: bool = True):
        self.chat_format = "chat_template.default"
        self.public_calls = []
        self.handler_calls = []
        self._chat_handlers = {}
        if with_metadata_handler:
            self._chat_handlers[self.chat_format] = self._handler

    def _handler(self, **kwargs):
        self.handler_calls.append(dict(kwargs))
        if kwargs["stream"]:
            return iter([{"choices": [{"delta": {"content": "ok"}}]}])
        return {"choices": [{"message": {"content": "ok"}}]}

    def create_chat_completion(self, **kwargs):
        self.public_calls.append(dict(kwargs))
        if kwargs["stream"]:
            return iter([{"choices": [{"delta": {"content": "fallback"}}]}])
        return {"choices": [{"message": {"content": "fallback"}}]}


def _payload(enable_thinking=None):
    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "model": "org/demo",
        "temperature": 0.0,
    }
    if enable_thinking is not None:
        payload["enable_thinking"] = enable_thinking
    return payload


def test_unspecified_thinking_uses_normal_public_completion_path():
    llm = _FakeLlama()

    result = chat_completion(llm, _payload(), stream=False)

    assert result["choices"][0]["message"]["content"] == "fallback"
    assert llm.handler_calls == []
    assert llm.public_calls[0]["stream"] is False
    assert "enable_thinking" not in llm.public_calls[0]


def test_explicit_false_reaches_metadata_jinja_handler_not_public_api():
    llm = _FakeLlama()

    result = chat_completion(llm, _payload(False), stream=False)

    assert result["choices"][0]["message"]["content"] == "ok"
    assert llm.public_calls == []
    call = llm.handler_calls[0]
    assert call["llama"] is llm
    assert call["enable_thinking"] is False
    assert call["stream"] is False
    assert call["messages"] == [{"role": "user", "content": "hello"}]


def test_explicit_true_reaches_same_handler_for_streaming_request():
    llm = _FakeLlama()

    chunks = list(chat_completion(llm, _payload(True), stream=True))

    assert chunks[0]["choices"][0]["delta"]["content"] == "ok"
    assert llm.public_calls == []
    assert llm.handler_calls[0]["enable_thinking"] is True
    assert llm.handler_calls[0]["stream"] is True


def test_custom_or_unproven_handler_fails_closed_instead_of_dropping_toggle():
    llm = _FakeLlama(with_metadata_handler=False)
    llm.chat_handler = lambda **_kwargs: None

    try:
        chat_completion(llm, _payload(False), stream=False)
    except LlamaCppThinkingControlError as exc:
        assert "metadata-backed" in str(exc)
    else:
        raise AssertionError("expected unproven llama_cpp handler to fail closed")

    assert llm.public_calls == []
