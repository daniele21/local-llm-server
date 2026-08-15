from __future__ import annotations

from local_llm_server.runtime_identity import (
    BackendIdentity,
    HardwareProfile,
    build_runtime_fingerprint,
    resolved_config_digest,
)


def _hardware() -> HardwareProfile:
    return HardwareProfile(
        system="darwin",
        machine="arm64",
        processor="apple",
        logical_cpus=10,
        total_memory_bytes=16 * 1024**3,
        accelerator="apple-gpu",
    )


def test_config_digest_ignores_private_paths_urls_and_unrelated_fields():
    base = {
        "backend": "mlx",
        "ctx_size": 4096,
        "n_threads": 8,
        "model_path": "/Users/private/model",
        "download_url": "https://secret.example/model",
        "prompt": "private",
    }
    changed_private = {
        **base,
        "model_path": "/another/private/path",
        "download_url": "https://different.example/model",
        "prompt": "different private prompt",
    }

    assert resolved_config_digest(base) == resolved_config_digest(changed_private)


def test_effective_runtime_config_change_changes_digest():
    first = resolved_config_digest({"backend": "llama_cpp", "ctx_size": 4096})
    second = resolved_config_digest({"backend": "llama_cpp", "ctx_size": 8192})
    assert first != second


def test_runtime_fingerprint_changes_with_backend_or_hardware():
    artifact_key = "a" * 64
    config = {"backend": "mlx", "ctx_size": 4096}
    first = build_runtime_fingerprint(
        artifact_key=artifact_key,
        backend=BackendIdentity("mlx", "1.0"),
        resolved_config=config,
        hardware=_hardware(),
    )
    second = build_runtime_fingerprint(
        artifact_key=artifact_key,
        backend=BackendIdentity("mlx", "2.0"),
        resolved_config=config,
        hardware=_hardware(),
    )

    assert first.stable_key() != second.stable_key()


def test_runtime_fingerprint_payload_contains_no_hostname_or_path():
    fingerprint = build_runtime_fingerprint(
        artifact_key="b" * 64,
        backend=BackendIdentity("llama_cpp", "0.3", "llama-cpp-python"),
        resolved_config={
            "backend": "llama_cpp",
            "ctx_size": 4096,
            "model_path": "/Users/daniele/private.gguf",
        },
        hardware=_hardware(),
    )

    payload = str(fingerprint.stable_payload())
    assert "/Users/" not in payload
    assert "hostname" not in payload.lower()


def test_stable_key_is_deterministic():
    fingerprint = build_runtime_fingerprint(
        artifact_key="c" * 64,
        backend=BackendIdentity("mlx", None),
        resolved_config={"backend": "mlx", "ctx_size": 4096},
        hardware=_hardware(),
    )

    assert fingerprint.stable_key() == fingerprint.stable_key()
