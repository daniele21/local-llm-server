"""Audio helpers for multimodal OpenAI-compatible requests."""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any


def _load_audio_dependencies() -> tuple[Any, Any]:
    try:
        import numpy as np
        import soundfile as sf
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            'Audio support requires optional dependencies. Install with: pip install "local-llm-server[audio]"'
        ) from exc
    return np, sf


def prepare_audio(input_path: str | Path) -> Path:
    """
    Convert an audio file to temporary 16 kHz mono WAV and return its path.
    """
    np, sf = _load_audio_dependencies()
    source = Path(input_path).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"Audio file not found: {source}")

    data, sample_rate = sf.read(str(source), always_2d=True)
    mono = data.mean(axis=1)
    target_rate = 16_000

    if int(sample_rate) != target_rate:
        duration = len(mono) / float(sample_rate)
        target_len = max(1, int(round(duration * target_rate)))
        source_x = np.linspace(0.0, duration, num=len(mono), endpoint=False)
        target_x = np.linspace(0.0, duration, num=target_len, endpoint=False)
        mono = np.interp(target_x, source_x, mono)

    mono = np.asarray(mono, dtype=np.float32)
    tmp = tempfile.NamedTemporaryFile(prefix="local-llm-audio-", suffix=".wav", delete=False)
    tmp.close()
    sf.write(tmp.name, mono, target_rate, subtype="PCM_16")
    return Path(tmp.name)


def audio_to_base64(wav_path: str | Path) -> str:
    """Read a WAV file and return its base64-encoded content."""
    path = Path(wav_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")
    return base64.b64encode(path.read_bytes()).decode("ascii")


def prepare_audio_message(audio_path: str | Path, prompt: str) -> list[dict[str, Any]]:
    """
    Build an OpenAI-compatible multimodal message containing WAV audio and text.
    """
    wav_path = prepare_audio(audio_path)
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_to_base64(wav_path),
                        "format": "wav",
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]
