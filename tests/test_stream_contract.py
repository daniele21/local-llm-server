from __future__ import annotations

from local_llm_server.stream_contract import StreamContractEngine, ensure_stream_contract


class _Engine:
    backend = "fake"

    def stream(self, payload):
        yield {"choices": [{"delta": {"content": "hello"}}]}
        yield {
            "choices": [],
            "usage": {"completion_tokens": 2},
            "timings": {"predicted_ms": 10.0},
        }

    def complete(self, payload):
        return {"choices": [{"message": {"content": "hello"}}]}

    def close(self):
        self.closed = True


def test_metrics_only_event_gets_empty_choice_without_inventing_content():
    wrapped = StreamContractEngine(_Engine())

    chunks = list(wrapped.stream({}))

    terminal = chunks[1]
    assert terminal["usage"] == {"completion_tokens": 2}
    assert terminal["timings"] == {"predicted_ms": 10.0}
    assert terminal["choices"] == [
        {"index": 0, "delta": {}, "finish_reason": None}
    ]


def test_text_event_is_not_rewritten():
    wrapped = StreamContractEngine(_Engine())
    first = next(wrapped.stream({}))
    assert first == {"choices": [{"delta": {"content": "hello"}}]}


def test_stream_contract_wrapper_is_idempotent():
    wrapped = ensure_stream_contract(_Engine())
    assert ensure_stream_contract(wrapped) is wrapped
