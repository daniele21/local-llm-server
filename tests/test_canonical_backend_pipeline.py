from __future__ import annotations

from local_llm_server.request_pipeline import prepare_chat_request


def test_prepare_chat_request_produces_canonical_and_backend_views_together():
    prepared = prepare_chat_request(
        {
            "model": "demo",
            "messages": [{"role": "user", "content": "hello"}],
            "max_output_tokens": 32,
            "show_reasoning": True,
        },
        runtime_config={
            "model": "demo",
            "model_id": "org/demo",
            "modalities": ["text"],
            "thinking_mode": "switchable",
            "enable_thinking": False,
            "show_thinking": False,
            "default_temperature": 0.0,
            "default_top_p": 0.8,
            "default_top_k": 20,
            "default_min_p": 0.0,
            "default_repeat_penalty": 1.0,
            "force_json": False,
        },
    )

    assert prepared.canonical.model == "demo"
    assert prepared.backend.kwargs["model"] == "org/demo"
    assert prepared.backend.kwargs["max_tokens"] == 32
    assert prepared.backend.max_tokens == 32
    assert prepared.backend.show_thinking is True
    assert prepared.messages == ({"role": "user", "content": "hello"},)


def test_prepare_chat_request_uses_explicit_resident_model_id_when_supplied():
    prepared = prepare_chat_request(
        {"input": "hello", "model": "alias"},
        runtime_config={"model": "alias", "modalities": ["text"]},
        runtime_model_id="org/exact-artifact",
    )

    assert prepared.backend.kwargs["model"] == "org/exact-artifact"
