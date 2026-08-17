from __future__ import annotations

import json

from local_llm_server.artifact_verification import (
    ArtifactVerificationStore,
    public_verification_summary,
    verify_model_artifact,
)
from local_llm_server.model_sources import ResolvedModel


def test_verify_model_artifact_hashes_once_and_persists_receipt(monkeypatch, tmp_path):
    artifact = tmp_path / "model.gguf"
    artifact.write_bytes(b"model-bytes")
    models_dir = tmp_path / "models"
    monkeypatch.setattr(
        "local_llm_server.artifact_verification.load_registry",
        lambda: {
            "models_dir": models_dir,
            "models": {
                "demo": {
                    "model_id": "org/demo",
                    "backend": "llama_cpp",
                    "filename": "model.gguf",
                }
            },
        },
    )
    monkeypatch.setattr(
        "local_llm_server.artifact_verification.resolve_registry_model",
        lambda *args, **kwargs: ResolvedModel(
            str(artifact), artifact, "managed", True
        ),
    )
    store = ArtifactVerificationStore(tmp_path / "receipts")

    receipt = verify_model_artifact("demo", store=store)

    assert len(receipt.sha256) == 64
    assert store.valid_for_file("org/demo", artifact) == receipt
    rendered = json.dumps(public_verification_summary(receipt))
    assert str(tmp_path) not in rendered


def test_verify_model_artifact_refuses_multi_file_directory(monkeypatch, tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    monkeypatch.setattr(
        "local_llm_server.artifact_verification.load_registry",
        lambda: {
            "models_dir": tmp_path,
            "models": {"demo": {"model_id": "org/demo", "backend": "mlx"}},
        },
    )
    monkeypatch.setattr(
        "local_llm_server.artifact_verification.resolve_registry_model",
        lambda *args, **kwargs: ResolvedModel(
            str(snapshot), snapshot, "managed", True
        ),
    )

    try:
        verify_model_artifact(
            "demo",
            store=ArtifactVerificationStore(tmp_path / "receipts"),
        )
    except ValueError as exc:
        assert "single-file" in str(exc)
    else:
        raise AssertionError("expected directory verification to fail closed")


def test_cli_source_exposes_verify_artifact_command():
    from pathlib import Path
    import local_llm_server.cli as cli

    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert 'sub.add_parser(\n        "verify-artifact"' in source
    assert 'elif args.command == "verify-artifact"' in source
