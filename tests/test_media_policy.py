from __future__ import annotations

import pytest

from local_llm_server.media_policy import (
    RemoteMediaPolicyError,
    validate_media_sources,
)


def test_remote_image_url_is_rejected_by_default():
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.png"},
                }
            ],
        }
    ]

    with pytest.raises(RemoteMediaPolicyError) as exc_info:
        validate_media_sources(messages)

    assert exc_info.value.urls == ("https://example.com/image.png",)


def test_data_url_is_allowed_by_default():
    validate_media_sources(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,AAAA"},
                    }
                ],
            }
        ]
    )


def test_remote_media_can_be_explicitly_enabled():
    validate_media_sources(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"url": "http://localhost/audio.wav"},
                    }
                ],
            }
        ],
        allow_remote_media=True,
    )
