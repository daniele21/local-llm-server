"""Deterministic residency eviction candidate selection.

This module selects candidates only. It never unloads runtimes by itself and it
never interprets successful unload as proof of host-memory reclamation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class EvictionMode(str, Enum):
    LRU = "lru"
    TTL = "ttl"


@dataclass(frozen=True, slots=True)
class EvictionPolicySettings:
    mode: EvictionMode
    limit: int = 1
    ttl_seconds: float | None = None
    protect_resident_default: bool = True

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.mode is EvictionMode.TTL:
            if self.ttl_seconds is None or self.ttl_seconds < 0:
                raise ValueError("ttl_seconds must be >= 0 for ttl mode")
        elif self.ttl_seconds is not None and self.ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0 when provided")


@dataclass(frozen=True, slots=True)
class EvictionCandidate:
    key: str
    model: str
    reason: EvictionMode
    last_used_age_seconds: float
    is_resident_default: bool

    def to_public_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "model": self.model,
            "reason": self.reason.value,
            "last_used_age_seconds": self.last_used_age_seconds,
            "is_resident_default": self.is_resident_default,
        }


def select_eviction_candidates(
    residency_snapshot: Mapping[str, Any],
    settings: EvictionPolicySettings,
) -> tuple[EvictionCandidate, ...]:
    """Return oldest eligible runtimes under an explicit eviction policy.

    Eligibility remains server-owned through the residency snapshot. This
    selector additionally protects the resident default unless the caller
    explicitly opts out, making automatic route changes impossible by default.
    """
    raw_runtimes = residency_snapshot.get("runtimes")
    if not isinstance(raw_runtimes, list):
        return ()

    candidates: list[EvictionCandidate] = []
    for item in raw_runtimes:
        if not isinstance(item, Mapping) or item.get("evictable") is not True:
            continue
        key = str(item.get("key") or "").strip()
        model = str(item.get("model") or key).strip()
        if not key:
            continue
        is_default = bool(item.get("is_resident_default"))
        if settings.protect_resident_default and is_default:
            continue
        try:
            age = float(item.get("last_used_age_seconds"))
        except (TypeError, ValueError):
            continue
        if age < 0:
            continue
        if settings.mode is EvictionMode.TTL:
            assert settings.ttl_seconds is not None
            if age < settings.ttl_seconds:
                continue
        candidates.append(
            EvictionCandidate(
                key=key,
                model=model,
                reason=settings.mode,
                last_used_age_seconds=age,
                is_resident_default=is_default,
            )
        )

    candidates.sort(key=lambda item: (-item.last_used_age_seconds, item.key))
    return tuple(candidates[: settings.limit])
