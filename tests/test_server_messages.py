from __future__ import annotations

from local_llm_server.server import _normalize_messages


def test_normalize_messages_preserves_multimodal_content():
    messages = _normalize_messages(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_audio", "input_audio": {"data": "abc", "format": "wav"}},
                        {"type": "text", "text": "Trascrivi"},
                    ],
                }
            ]
        }
    )

    assert messages[0]["content"][0]["type"] == "input_audio"


def test_normalize_messages_flattens_text_parts():
    messages = _normalize_messages(
        {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "A"},
                        {"type": "text", "text": "B"},
                    ],
                }
            ]
        }
    )

    assert messages == [{"role": "user", "content": "A\nB"}]
