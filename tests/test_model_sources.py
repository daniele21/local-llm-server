from __future__ import annotations

import json

import pytest

from local_llm_server.model_sources import (
    is_complete_mlx_model,
    resolve_mlx_runtime_path,
)


def _write_metadata(path, *, multimodal=True):
    path.mkdir()
    (path / "config.json").write_text("{}")
    (path / "tokenizer_config.json").write_text("{}")
    if multimodal:
        (path / "preprocessor_config.json").write_text("{}")


def test_complete_mlx_model_accepts_lmstudio_consolidated_weights(tmp_path):
    model = tmp_path / "model"
    _write_metadata(model)
    (model / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"a": "missing-shard.safetensors"}})
    )
    (model / "model.safetensors").write_bytes(b"weights")

    assert is_complete_mlx_model(model, multimodal=True)


def test_complete_mlx_model_requires_every_referenced_shard(tmp_path):
    model = tmp_path / "model"
    _write_metadata(model)
    (model / "model.safetensors.index.json").write_text(json.dumps({
        "weight_map": {
            "a": "model-00001-of-00002.safetensors",
            "b": "model-00002-of-00002.safetensors",
        }
    }))
    (model / "model-00001-of-00002.safetensors").write_bytes(b"one")

    assert not is_complete_mlx_model(model, multimodal=True)
    (model / "model-00002-of-00002.safetensors").write_bytes(b"two")
    assert is_complete_mlx_model(model, multimodal=True)


def test_no_download_rejects_incomplete_huggingface_cache(monkeypatch, tmp_path):
    incomplete = tmp_path / "snapshot"
    _write_metadata(incomplete)

    monkeypatch.setattr(
        "huggingface_hub.snapshot_download",
        lambda **_kwargs: str(incomplete),
    )

    with pytest.raises(FileNotFoundError, match="not fully cached"):
        resolve_mlx_runtime_path(
            "org/model", no_download=True, multimodal=True
        )


def test_huggingface_download_is_resolved_before_backend_start(monkeypatch, tmp_path):
    snapshot = tmp_path / "snapshot"
    _write_metadata(snapshot)
    (snapshot / "model.safetensors").write_bytes(b"weights")
    calls = []

    def snapshot_download(**kwargs):
        calls.append(kwargs)
        if kwargs.get("local_files_only"):
            raise FileNotFoundError("not cached")
        return str(snapshot)

    monkeypatch.setattr("huggingface_hub.snapshot_download", snapshot_download)

    resolved = resolve_mlx_runtime_path(
        "org/model", no_download=False, multimodal=True
    )

    assert resolved == snapshot
    assert calls == [
        {"repo_id": "org/model", "local_files_only": True},
        {"repo_id": "org/model"},
    ]
