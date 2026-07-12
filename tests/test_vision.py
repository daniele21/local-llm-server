from __future__ import annotations

import base64

import pytest

from local_llm_server.vision import image_to_data_url, prepare_image_message


def test_image_to_data_url(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    assert image_to_data_url(image) == "data:image/png;base64," + base64.b64encode(b"png").decode("ascii")


def test_image_to_data_url_rejects_unsupported_type(tmp_path):
    image = tmp_path / "image.gif"
    image.write_bytes(b"gif")

    with pytest.raises(ValueError, match="Unsupported image type"):
        image_to_data_url(image)


def test_image_to_data_url_enforces_size_limit(tmp_path):
    image = tmp_path / "image.webp"
    image.write_bytes(b"1234")

    with pytest.raises(ValueError, match="Image is too large"):
        image_to_data_url(image, max_bytes=3)


def test_prepare_image_message(tmp_path):
    image = tmp_path / "image.jpg"
    image.write_bytes(b"jpg")

    messages = prepare_image_message(image, "Descrivi")

    assert messages[0]["role"] == "user"
    assert messages[0]["content"][0]["type"] == "image_url"
    assert messages[0]["content"][1] == {"type": "text", "text": "Descrivi"}
