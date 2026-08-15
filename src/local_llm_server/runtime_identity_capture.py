"""Controlled automatic runtime-identity capture for evidence-grade runs.

Automatic attachment is deliberately conservative: a runtime receives a
product fingerprint only when the model artifact has an explicit SHA-256 pin
and the backend implementation version can be resolved. Otherwise execution is
allowed but evidence remains exploratory.
"""
from __future__ import annotations

from typing import Any, Mapping

from .artifact_identity import (
    ArtifactIdentity,
    ArtifactSourceKind,
    ArtifactVerificationState,
)
from .runtime_evidence import RuntimeIdentitySnapshot, build_and_attach_runtime_identity
from .runtime_identity import backend_identity, local_hardware_profile


_BACKEND_PACKAGES: dict[str, str] = {
    "llama_cpp": "llama-cpp-python",
    "mlx": "mlx-lm",
    "mlx_vlm_server": "mlx-vlm",
}


def capture_verified_runtime_identity(
    runtime: Any,
    *,
    total_memory_bytes: int | None = None,
    accelerator: str | None = None,
) -> RuntimeIdentitySnapshot | None:
    """Attach identity once when artifact + backend evidence is strong enough."""
    cfg: Mapping[str, Any] = getattr(runtime, "cfg", {})
    sha256 = cfg.get("artifact_sha256")
    if not isinstance(sha256, str) or not _valid_sha256(sha256):
        return None

    backend_name = str(cfg.get("backend") or getattr(runtime.engine, "backend", "unknown"))
    package_name = _BACKEND_PACKAGES.get(backend_name)
    if package_name is None:
        # Managed llama-server binaries and unknown engines need an explicit
        # binary/version probe before they qualify for automatic evidence-grade identity.
        return None

    backend = backend_identity(
        backend_name,
        package_name=package_name,
        implementation=runtime.engine.__class__.__name__,
    )
    if backend.version is None:
        return None

    source_kind = _source_kind(cfg.get("model_source"))
    logical_id = str(cfg.get("model_id") or cfg.get("model") or runtime.key)
    artifact = ArtifactIdentity(
        logical_id=logical_id,
        source_kind=source_kind,
        source_ref=logical_id,
        revision=(
            str(cfg["artifact_revision"])
            if cfg.get("artifact_revision") is not None
            else None
        ),
        sha256=sha256.lower(),
        verification=ArtifactVerificationState.VERIFIED,
    )

    return build_and_attach_runtime_identity(
        runtime,
        artifact_key=artifact.stable_key(),
        backend=backend,
        hardware=local_hardware_profile(
            total_memory_bytes=total_memory_bytes,
            accelerator=accelerator,
        ),
        resolved_config=cfg,
    )


def _source_kind(value: Any) -> ArtifactSourceKind:
    try:
        return ArtifactSourceKind(str(value))
    except ValueError:
        return ArtifactSourceKind.UNRESOLVED


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())
