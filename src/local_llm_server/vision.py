"""Image helpers for OpenAI-compatible multimodal requests."""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DEFAULT_MAX_IMAGE_BYTES = 10 * 1024 * 1024


def image_to_data_url(
    image_path: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
) -> str:
    """Encode a supported local image as a data URL."""
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    mime_type = mimetypes.guess_type(path.name)[0]
    if mime_type not in SUPPORTED_IMAGE_TYPES:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_TYPES))
        raise ValueError(
            f"Unsupported image type: {mime_type or 'unknown'}. Supported types: {supported}"
        )

    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"Image is too large: {size / 1024 / 1024:.1f} MB. "
            f"Maximum allowed: {max_bytes / 1024 / 1024:.1f} MB."
        )

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def prepare_image_message(image_path: str | Path, prompt: str) -> list[dict[str, Any]]:
    """Build one OpenAI-compatible user message containing an image and prompt."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
