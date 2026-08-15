from __future__ import annotations

import hashlib

from local_llm_server.artifact_identity import (
    ArtifactSourceKind,
    VerificationState,
    identify_resolved_artifact,
    sha256_file,
)
from local_llm_server.model_sources import ResolvedModel


def test_explicit_file_can_be_verified_by_digest(tmp_path):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"model-bytes")
    resolved = ResolvedModel(str(model), model, "explicit", True)

    identity = identify_resolved_artifact(
        "demo",
        {"filename": "model.gguf", "model_id": "org/demo"},
        resolved,
        hash_local_file=True,
    )

    assert identity.source_kind is ArtifactSourceKind.EXPLICIT
    assert identity.sha256 == hashlib.sha256(b"model-bytes").hexdigest()
    assert identity.size_bytes == len(b"model-bytes")
    assert identity.verification is VerificationState.VERIFIED
    assert str(tmp_path) not in str(identity.stable_payload())


def test_available_directory_is_not_falsely_marked_verified(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    resolved = ResolvedModel(str(snapshot), snapshot, "huggingface", True)

    identity = identify_resolved_artifact(
        "demo",
        {"model_id": "org/demo", "revision": "abc123"},
        resolved,
    )

    assert identity.source_ref == "org/demo"
    assert identity.revision == "abc123"
    assert identity.sha256 is None
    assert identity.verification is VerificationState.AVAILABLE_UNVERIFIED


def test_unavailable_artifact_is_explicit():
    resolved = ResolvedModel("org/demo", None, "huggingface", False)
    identity = identify_resolved_artifact("demo", {"model_id": "org/demo"}, resolved)
    assert identity.verification is VerificationState.UNAVAILABLE


def test_stable_key_changes_when_digest_changes(tmp_path):
    first = tmp_path / "first.gguf"
    second = tmp_path / "second.gguf"
    first.write_bytes(b"one")
    second.write_bytes(b"two")

    a = identify_resolved_artifact(
        "same",
        {"filename": "model.gguf"},
        ResolvedModel(str(first), first, "managed", True),
        hash_local_file=True,
    )
    b = identify_resolved_artifact(
        "same",
        {"filename": "model.gguf"},
        ResolvedModel(str(second), second, "managed", True),
        hash_local_file=True,
    )

    assert a.stable_key() != b.stable_key()


def test_sha256_file_is_deterministic(tmp_path):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == hashlib.sha256(b"abc").hexdigest()
