from types import SimpleNamespace

import pytest

from local_llm_server.runtime_evidence import (
    attached_runtime_identity,
    build_and_attach_runtime_identity,
)
from local_llm_server.runtime_identity import BackendIdentity, HardwareProfile


ARTIFACT_KEY = "a" * 64


def test_build_and_attach_runtime_identity_uses_runtime_config_and_is_public_safe():
    runtime = SimpleNamespace(
        cfg={
            "backend": "llama_cpp",
            "ctx_size": 4096,
            "model_path": "/private/models/demo.gguf",
            "download_url": "https://example.invalid/private",
        }
    )
    snapshot = build_and_attach_runtime_identity(
        runtime,
        artifact_key=ARTIFACT_KEY,
        backend=BackendIdentity("llama_cpp", version="1.0"),
        hardware=HardwareProfile(
            system="linux",
            machine="x86_64",
            processor="cpu",
            logical_cpus=8,
            total_memory_bytes=16_000,
        ),
        captured_at=123.0,
    )

    assert attached_runtime_identity(runtime) is snapshot
    public = snapshot.to_public_dict()
    assert public["fingerprint"] == snapshot.fingerprint
    assert public["captured_at"] == 123.0
    rendered = str(public)
    assert "/private/models" not in rendered
    assert "example.invalid" not in rendered


def test_attachment_is_immutable_within_one_residency_by_default():
    runtime = SimpleNamespace(cfg={"backend": "mlx", "max_kv_size": 1024})
    first = build_and_attach_runtime_identity(
        runtime,
        artifact_key=ARTIFACT_KEY,
        backend=BackendIdentity("mlx"),
        hardware=HardwareProfile("darwin", "arm64", None, 10),
        captured_at=1.0,
    )

    with pytest.raises(RuntimeError, match="already attached"):
        build_and_attach_runtime_identity(
            runtime,
            artifact_key=ARTIFACT_KEY,
            backend=BackendIdentity("mlx"),
            hardware=HardwareProfile("darwin", "arm64", None, 10),
            captured_at=2.0,
        )

    assert attached_runtime_identity(runtime) is first


def test_meaningful_config_change_changes_next_residency_fingerprint():
    runtime_a = SimpleNamespace(cfg={"backend": "llama_cpp", "ctx_size": 2048})
    runtime_b = SimpleNamespace(cfg={"backend": "llama_cpp", "ctx_size": 4096})
    hardware = HardwareProfile("linux", "x86_64", None, 4)
    backend = BackendIdentity("llama_cpp", version="1")

    a = build_and_attach_runtime_identity(
        runtime_a,
        artifact_key=ARTIFACT_KEY,
        backend=backend,
        hardware=hardware,
        captured_at=1.0,
    )
    b = build_and_attach_runtime_identity(
        runtime_b,
        artifact_key=ARTIFACT_KEY,
        backend=backend,
        hardware=hardware,
        captured_at=1.0,
    )

    assert a.fingerprint != b.fingerprint
