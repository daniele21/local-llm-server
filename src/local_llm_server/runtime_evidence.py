"""Controlled attachment of runtime identity to lifecycle/evidence objects.

Fingerprint capture is intentionally explicit. Callers should capture once at a
stable lifecycle point (for example immediately after a runtime becomes READY)
and reuse the attached snapshot for API/evaluation evidence rather than probing
package/hardware/artifact identity on every request.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from .runtime_identity import (
    BackendIdentity,
    HardwareProfile,
    RuntimeFingerprint,
    build_runtime_fingerprint,
)


@dataclass(frozen=True, slots=True)
class RuntimeIdentitySnapshot:
    fingerprint: str
    payload: Mapping[str, object]
    captured_at: float

    def __post_init__(self) -> None:
        digest = self.fingerprint.lower()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("fingerprint must be a SHA-256 hex digest")
        if self.captured_at < 0:
            raise ValueError("captured_at must be >= 0")

    def to_public_dict(self) -> dict[str, object]:
        return {
            "fingerprint": self.fingerprint,
            "captured_at": self.captured_at,
            "identity": dict(self.payload),
        }


def snapshot_runtime_fingerprint(
    fingerprint: RuntimeFingerprint,
    *,
    captured_at: float | None = None,
) -> RuntimeIdentitySnapshot:
    return RuntimeIdentitySnapshot(
        fingerprint=fingerprint.stable_key(),
        payload=fingerprint.stable_payload(),
        captured_at=time.time() if captured_at is None else captured_at,
    )


def attach_runtime_identity(
    runtime: Any,
    snapshot: RuntimeIdentitySnapshot,
    *,
    replace: bool = False,
) -> RuntimeIdentitySnapshot:
    """Attach one immutable snapshot to a runtime object.

    Runtime classes are intentionally not required to import the identity layer.
    Replacing an existing attachment is rejected by default so evidence cannot
    silently change during one residency period.
    """
    existing = getattr(runtime, "runtime_identity_snapshot", None)
    if existing is not None and not replace:
        raise RuntimeError("runtime identity snapshot is already attached")
    runtime.runtime_identity_snapshot = snapshot
    return snapshot


def attached_runtime_identity(runtime: Any) -> RuntimeIdentitySnapshot | None:
    snapshot = getattr(runtime, "runtime_identity_snapshot", None)
    return snapshot if isinstance(snapshot, RuntimeIdentitySnapshot) else None


def build_and_attach_runtime_identity(
    runtime: Any,
    *,
    artifact_key: str,
    backend: BackendIdentity,
    hardware: HardwareProfile,
    resolved_config: Mapping[str, Any] | None = None,
    captured_at: float | None = None,
) -> RuntimeIdentitySnapshot:
    config = resolved_config if resolved_config is not None else getattr(runtime, "cfg", {})
    fingerprint = build_runtime_fingerprint(
        artifact_key=artifact_key,
        backend=backend,
        resolved_config=config,
        hardware=hardware,
    )
    return attach_runtime_identity(
        runtime,
        snapshot_runtime_fingerprint(fingerprint, captured_at=captured_at),
    )
