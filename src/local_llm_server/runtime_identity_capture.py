"""Controlled automatic runtime-identity capture for evidence-grade runs.

Automatic attachment is deliberately conservative: a runtime receives a
product fingerprint only when the model artifact has strong SHA-256 evidence
and the backend implementation version can be resolved. Strong artifact
evidence may come from an explicit config pin or from a locally persisted
verification receipt that still matches the exact current file.
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
from .artifact_verification import ArtifactVerificationStore
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
    verification_store: ArtifactVerificationStore | None = None,
) -> RuntimeIdentitySnapshot | None:
    """Attach identity once when artifact + backend evidence is strong enough."""
    cfg: Mapping[str, Any] = getattr(runtime, "cfg", {})
    logical_id = str(cfg.get("model_id") or cfg.get("model") or runtime.key)
    sha256, size_bytes = _verified_artifact_evidence(
        cfg,
        logical_id=logical_id,
        store=verification_store,
    )
    if sha256 is None:
        return None

    backend = resolve_backend_identity(runtime)
    if backend is None or backend.version is None:
        return None

    source_kind = _source_kind(cfg.get("model_source"))
    artifact = ArtifactIdentity(
        logical_id=logical_id,
        source_kind=source_kind,
        source_ref=logical_id,
        revision=(
            str(cfg["artifact_revision"])
            if cfg.get("artifact_revision") is not None
            else None
        ),
        sha256=sha256,
        size_bytes=size_bytes,
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


def resolve_backend_identity(runtime: Any) -> BackendIdentity | None:
    """Resolve the effective backend identity without requiring artifact verification."""
    cfg: Mapping[str, Any] = getattr(runtime, "cfg", {})
    backend_name = str(cfg.get("backend") or getattr(runtime.engine, "backend", "unknown"))
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


def _verified_artifact_evidence(
    cfg: Mapping[str, Any],
    *,
    logical_id: str,
    store: ArtifactVerificationStore | None,
) -> tuple[str | None, int | None]:
    explicit = cfg.get("artifact_sha256")
    if isinstance(explicit, str) and _valid_sha256(explicit):
        return explicit.lower(), _optional_size(cfg.get("artifact_size_bytes"))

    model_path = cfg.get("model_path")
    if not isinstance(model_path, str) or not model_path:
        return None, None
    path = Path(model_path).expanduser()
    if not path.is_file():
        return None, None

    receipt = (store or ArtifactVerificationStore()).valid_for_file(logical_id, path)
    if receipt is None:
        return None, None
    return receipt.sha256, receipt.size_bytes


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


def _optional_size(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
