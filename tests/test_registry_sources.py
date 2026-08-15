from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from local_llm_server.registry import load_registry


def test_explicit_external_registry_is_merged_without_consumer_coupling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    external = tmp_path / "consumer-registry.json"
    external.write_text(
        json.dumps(
            {
                "models": {
                    "consumer-model": {
                        "filename": "consumer.gguf",
                        "model_id": "consumer/model",
                        "params": {"ctx_size": 2048, "n_threads": 3},
                    }
                },
                "default_model": "consumer-model",
                "startup_models": ["consumer-model"],
                "defaults": {"n_threads": 2},
            }
        ),
        encoding="utf-8",
    )

    registry = load_registry(extra_registry_paths=[external])

    assert registry["default_model"] == "consumer-model"
    assert registry["startup_models"] == ["consumer-model"]
    assert registry["models"]["consumer-model"]["model_id"] == "consumer/model"
    assert registry["models"]["consumer-model"]["params"]["ctx_size"] == 2048
    assert registry["defaults"]["n_threads"] == 2


def test_environment_registry_paths_support_multiple_layers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.json"
    first.write_text(
        """
models:
  external:
    filename: external.gguf
    params:
      ctx_size: 1024
default_model: external
""".strip(),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "models": {"external": {"params": {"ctx_size": 4096}}},
                "startup_models": ["external"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "LOCAL_LLM_REGISTRY_PATHS",
        f"{first}{os.pathsep}{second}",
    )

    registry = load_registry()

    assert registry["models"]["external"]["params"]["ctx_size"] == 4096
    assert registry["startup_models"] == ["external"]


def test_missing_external_registry_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    with pytest.raises(FileNotFoundError, match="External registry not found"):
        load_registry(extra_registry_paths=[tmp_path / "missing.yaml"])
