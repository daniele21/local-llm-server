from __future__ import annotations

from types import SimpleNamespace

from local_llm_server.artifact_identity import ArtifactVerificationReceipt, sha256_file
from local_llm_server.artifact_verification import (
    ArtifactVerificationStore,
    public_verification_summary,
)
from local_llm_server.runtime_evidence import attached_runtime_identity
from local_llm_server.runtime_identity import BackendIdentity
from local_llm_server.runtime_identity_capture import capture_verified_runtime_identity


class _Engine:
    backend = "llama_cpp"


def test_store_round_trip_and_public_summary_never_expose_path(tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"verified-model")
    receipt = ArtifactVerificationReceipt.for_file(
        "org/demo",
        artifact,
        sha256=sha256_file(artifact),
    )
    store = ArtifactVerificationStore(tmp_path / "receipts")

    stored_path = store.save(receipt)
    restored = store.valid_for_file("org/demo", artifact)

    assert stored_path.is_file()
    assert restored == receipt
    summary = public_verification_summary(receipt)
    assert summary["verification"] == "verified"
    assert summary["sha256"] == receipt.sha256
    assert str(tmp_path) not in str(summary)
    assert "artifact_path" not in summary


def test_changed_file_invalidates_cached_receipt(tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"first")
    store = ArtifactVerificationStore(tmp_path / "receipts")
    receipt = ArtifactVerificationReceipt.for_file(
        "org/demo",
        artifact,
        sha256=sha256_file(artifact),
    )
    store.save(receipt)

    artifact.write_bytes(b"replacement-is-different")

    assert store.valid_for_file("org/demo", artifact) is None


def test_runtime_identity_uses_valid_receipt_when_config_has_no_digest(monkeypatch, tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"model")
    store = ArtifactVerificationStore(tmp_path / "receipts")
    receipt = ArtifactVerificationReceipt.for_file(
        "org/demo",
        artifact,
        sha256=sha256_file(artifact),
    )
    store.save(receipt)
    monkeypatch.setattr(
        "local_llm_server.runtime_identity_capture.backend_identity",
        lambda *args, **kwargs: BackendIdentity(
            name="llama_cpp",
            implementation="_Engine",
            version="1.2.3",
        ),
    )
    runtime = SimpleNamespace(
        key="demo",
        cfg={
            "model": "demo",
            "model_id": "org/demo",
            "model_path": str(artifact),
            "model_source": "managed",
            "backend": "llama_cpp",
            "ctx_size": 4096,
            "max_concurrent_requests": 1,
            "artifact_sha256": None,
        },
        engine=_Engine(),
    )

    snapshot = capture_verified_runtime_identity(runtime, verification_store=store)

    assert snapshot is not None
    assert attached_runtime_identity(runtime) is snapshot
    public = snapshot.to_public_dict()
    assert len(str(public["identity"]["artifact_key"])) == 64
    assert public["identity"]["backend"]["version"] == "1.2.3"
    assert str(artifact) not in str(public)


def test_runtime_identity_refuses_stale_receipt(monkeypatch, tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"model")
    store = ArtifactVerificationStore(tmp_path / "receipts")
    store.save(
        ArtifactVerificationReceipt.for_file(
            "org/demo",
            artifact,
            sha256=sha256_file(artifact),
        )
    )
    artifact.write_bytes(b"changed")
    runtime = SimpleNamespace(
        key="demo",
        cfg={
            "model": "demo",
            "model_id": "org/demo",
            "model_path": str(artifact),
            "model_source": "managed",
            "backend": "llama_cpp",
            "artifact_sha256": None,
        },
        engine=_Engine(),
    )

    assert capture_verified_runtime_identity(runtime, verification_store=store) is None
    assert attached_runtime_identity(runtime) is None
