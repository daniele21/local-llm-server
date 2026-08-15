"""Privacy policy helpers for multimodal request sources."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class RemoteMediaPolicyError(ValueError):
    urls: tuple[str, ...]

    def __str__(self) -> str:
        return (
            "Remote HTTP(S) media is disabled by local privacy policy. "
            "Provide local/data-URL media or explicitly enable remote media."
        )


def validate_media_sources(
    messages: Sequence[Mapping[str, Any]],
    *,
    allow_remote_media: bool = False,
) -> None:
    """Reject HTTP(S) media references unless the caller opted in explicitly."""
    if allow_remote_media:
        return

    remote_urls = tuple(_remote_media_urls(messages))
    if remote_urls:
        raise RemoteMediaPolicyError(remote_urls)


def _remote_media_urls(messages: Sequence[Mapping[str, Any]]):
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, Mapping):
                continue
            part_type = str(part.get("type") or "")
            if part_type not in {
                "image",
                "image_url",
                "input_image",
                "audio",
                "input_audio",
            }:
                continue
            for candidate in _candidate_urls(part):
                parsed = urlparse(candidate)
                if parsed.scheme.lower() in {"http", "https"}:
                    yield candidate


def _candidate_urls(value: Any):
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key == "url" and isinstance(child, str):
                yield child
            else:
                yield from _candidate_urls(child)
    elif isinstance(value, list):
        for child in value:
            yield from _candidate_urls(child)
