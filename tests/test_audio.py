from __future__ import annotations

import base64

from local_llm_server.audio import audio_to_base64, prepare_audio_message


def test_audio_to_base64(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"abc")

    assert audio_to_base64(wav) == base64.b64encode(b"abc").decode("ascii")


def test_prepare_audio_message_uses_prepared_wav(monkeypatch, tmp_path):
    wav = tmp_path / "prepared.wav"
    wav.write_bytes(b"wav")

    monkeypatch.setattr("local_llm_server.audio.prepare_audio", lambda _path: wav)

    message = prepare_audio_message("input.mp3", "Analizza")

    assert message[0]["role"] == "user"
    content = message[0]["content"]
    assert content[0]["type"] == "input_audio"
    assert content[0]["input_audio"]["format"] == "wav"
    assert content[0]["input_audio"]["data"] == base64.b64encode(b"wav").decode("ascii")
    assert content[1] == {"type": "text", "text": "Analizza"}
