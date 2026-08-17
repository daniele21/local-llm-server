"""Stable identity for model artifacts independently from runtime residency.

Artifact identity is intentionally separate from backend/config/hardware identity.
D3 composes those later into a runtime fingerprint. Explicit verification
receipts are local-only cache records and never part of the public identity
payload because they contain a private filesystem path and stat metadata.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .model_sources import ResolvedModel


class ArtifactSourceKind(str, Enum):
    EXPLICIT = "explicit"
    LM_STUDIO = "lmstudio"
    MANAGED = "managed"
    HUGGING_FACE = "huggingface"
    UNRESOLVED = "unresolved"


class VerificationState(str, Enum):
    VERIFIED = "verified"
    AVAILABLE_UNVERIFIED = "available_unverified"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ArtifactIdentity:
    logical_id: str
    source_kind: ArtifactSourceKind
    source_ref: str
    revision: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    verification: VerificationState = VerificationState.AVAILABLE_UNVERIFIED

    def __post_init__(self) -> None:
        if not self.logical_id.strip():
            raise ValueError("logical_id must be non-empty")
        if not self.source_ref.strip():
            raise ValueError("source_ref must be non-empty")
        if self.sha256 is not None:
            _validate_sha256(self.sha256)
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")
        if self.verification is VerificationState.VERIFIED and self.sha256 is None:
            raise ValueError("verified artifact identity requires sha256")

    def stable_payload(self) -> dict[str, object]:
        """Path-free representation suitable for persistence/API/evidence."""
        return {
            "logical_id": self.logical_id,
            "source_kind": self.source_kind.value,
            "source_ref": self.source_ref,
            "revision": self.revision,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "verification": self.verification.value,
        }

    def stable_key(self) -> str:
        payload = json.dumps(self.stable_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactVerificationReceipt:
    """Local cache receipt for an explicitly hashed single-file artifact.

    ``artifact_path`` and stat fields are deliberately private/local metadata.
    Consumers may reuse the strong digest only while ``matches_file`` remains
    true. Directories and multi-file snapshots require a future manifest design
    and cannot be represented by this single-file receipt.
    """

    logical_id: str
    artifact_path: str
    sha256: str
    size_bytes: int
    mtime_ns: int
    inode: int | None = None
    device: int | None = None

    def __post_init__(self) -> None:
        if not self.logical_id.strip():
            raise ValueError("logical_id must be non-empty")
        if not self.artifact_path.strip():
            raise ValueError("artifact_path must be non-empty")
        _validate_sha256(self.sha256)
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0")
        if self.mtime_ns < 0:
            raise ValueError("mtime_ns must be >= 0")

    @classmethod
    def for_file(
        cls,
        logical_id: str,
        artifact_path: str | Path,
        *,
        sha256: str,
    ) -> "ArtifactVerificationReceipt":
        """Bind a caller-supplied strong digest to the current local file stamp."""
        path = Path(artifact_path).expanduser().resolve()
        if not path.is_file():
            raise ValueError("single-file verification receipt requires a regular file")
        stat = path.stat()
        return cls(
            logical_id=logical_id,
            artifact_path=str(path),
            sha256=sha256.lower(),
            size_bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
            inode=_optional_stat_int(stat.st_ino),
            device=_optional_stat_int(stat.st_dev),
        )

    def matches_file(self, artifact_path: str | Path | None = None) -> bool:
        """Return whether ordinary local replacement/change invalidates reuse."""
        path = Path(artifact_path or self.artifact_path).expanduser().resolve()
        if str(path) != self.artifact_path or not path.is_file():
            return False
        stat = path.stat()
        if stat.st_size != self.size_bytes or stat.st_mtime_ns != self.mtime_ns:
            return False
        if self.inode is not None and _optional_stat_int(stat.st_ino) != self.inode:
            return False
        if self.device is not None and _optional_stat_int(stat.st_dev) != self.device:
            return False
        return True

    def private_payload(self) -> dict[str, object]:
        """Serializable local-store form. Never expose through public APIs."""
        return {
            "logical_id": self.logical_id,
            "artifact_path": self.artifact_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
            "inode": self.inode,
            "device": self.device,
        }

    @classmethod
    def from_private_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> "ArtifactVerificationReceipt":
        return cls(
            logical_id=str(payload.get("logical_id") or ""),
            artifact_path=str(payload.get("artifact_path") or ""),
            sha256=str(payload.get("sha256") or "").lower(),
            size_bytes=int(payload.get("size_bytes", -1)),
            mtime_ns=int(payload.get("mtime_ns", -1)),
            inode=_optional_int(payload.get("inode")),
            device=_optional_int(payload.get("device")),
        )


def identify_resolved_artifact(
    key: str,
    entry: Mapping[str, Any],
    resolved: ResolvedModel,
    *,
    hash_local_file: bool = False,
) -> ArtifactIdentity:
    source_kind = ArtifactSourceKind(resolved.source_type)
    source_ref = _source_reference(key, entry, resolved)
    revision = _optional_text(entry.get("revision") or entry.get("hf_revision"))

    if not resolved.downloaded:
        return ArtifactIdentity(
            logical_id=str(entry.get("model_id") or key),
            source_kind=source_kind,
            source_ref=source_ref,
            revision=revision,
            verification=VerificationState.UNAVAILABLE,
        )

    digest = None
    size_bytes = None
    if hash_local_file and resolved.local_path is not None and resolved.local_path.is_file():
        digest = sha256_file(resolved.local_path)
        size_bytes = resolved.local_path.stat().st_size

    return ArtifactIdentity(
        logical_id=str(entry.get("model_id") or key),
        source_kind=source_kind,
        source_ref=source_ref,
        revision=revision,
        sha256=digest,
        size_bytes=size_bytes,
        verification=(
            VerificationState.VERIFIED
            if digest is not None
            else VerificationState.AVAILABLE_UNVERIFIED
        ),
    )


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Explicitly hash a concrete artifact file; never called implicitly by UI refresh."""
    artifact = Path(path)
    hasher = hashlib.sha256()
    with artifact.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _source_reference(key: str, entry: Mapping[str, Any], resolved: ResolvedModel) -> str:
    if resolved.source_type == "huggingface":
        return str(entry.get("model_id") or resolved.model_path or key)
    if resolved.source_type == "managed":
        return str(entry.get("filename") or key)
    if resolved.source_type == "lmstudio":
        return str(entry.get("lmstudio_path") or entry.get("filename") or key)
    if resolved.source_type == "explicit":
        # Do not serialize a private absolute path as identity. Prefer the
        # configured reference or filename and use digest for immutable identity.
        return str(entry.get("path") or entry.get("filename") or entry.get("model_id") or key)
    return str(entry.get("model_id") or key)


def _validate_sha256(value: str) -> None:
    digest = value.lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("sha256 must be a 64-character hexadecimal digest")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_stat_int(value: Any) -> int | None:
    parsed = int(value)
    return parsed if parsed != 0 else None
