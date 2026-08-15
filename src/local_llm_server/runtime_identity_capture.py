"""Controlled automatic runtime-identity capture for evidence-grade runs.

Automatic attachment is deliberately conservative: a runtime receives a
product fingerprint only when the model artifact has an explicit SHA-256 pin
and the backend implementation version can be resolved. Otherwise execution is
allowed but evidence remains exploratory.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .artifact_identity import (
    ArtifactIdentity,
    ArtifactSourceKind,
    VerificationState,
)
from .runtime_evidence import RuntimeIdentitySnapshot, build_and_attach_runtime_identity
from .runtime_identity import BackendIdentity, backend_identity, local_hardware_profile


_BACKEND_PACKAGES: dict[str, str] = {
    "llama_cpp": "llama-cpp-python",
    "mlx": "mlx-lm",
    "mlx_vlm_server": "mlx-vlm",
}
_LLAMA_SERVER_VERSION = re.compile(
    r"version:\s*(?P<build>\d+)\s*\(`?(?P<commit>[0-9a-fA-F]{7,40})`?\)"
)


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
    backend = _resolved_backend_identity(runtime, backend_name, cfg)
    if backend is None or backend.version is None:
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
        verification=VerificationState.VERIFIED,
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


def _resolved_backend_identity(
    runtime: Any,
    backend_name: str,
    cfg: Mapping[str, Any],
) -> BackendIdentity | None:
    implementation = runtime.engine.__class__.__name__
    package_name = _BACKEND_PACKAGES.get(backend_name)
    if package_name is not None:
        resolved = backend_identity(
            backend_name,
            package_name=package_name,
            implementation=implementation,
        )
        if resolved.version is not None:
            return resolved

    explicit = cfg.get("backend_version") or getattr(runtime.engine, "backend_version", None)
    if isinstance(explicit, str) and explicit.strip():
        return BackendIdentity(
            name=backend_name,
            version=explicit.strip(),
            implementation=implementation,
        )

    if backend_name == "llama_server":
        version = _probe_llama_server_version(getattr(runtime.engine, "binary", None))
        if version is not None:
            return BackendIdentity(
                name=backend_name,
                version=version,
                implementation=implementation,
            )
    return None


def _probe_llama_server_version(binary: Any) -> str | None:
    if binary is None:
        return None
    path = Path(str(binary)).expanduser()
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    match = _LLAMA_SERVER_VERSION.search(text)
    if match is None:
        return None
    return f"build-{match.group('build')}@{match.group('commit').lower()}"


def _source_kind(value: Any) -> ArtifactSourceKind:
    try:
        return ArtifactSourceKind(str(value))
    except ValueError:
        return ArtifactSourceKind.UNRESOLVED


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(ch in "0123456789abcdef" for ch in value.lower())
