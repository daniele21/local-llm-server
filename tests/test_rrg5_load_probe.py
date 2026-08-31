from __future__ import annotations

from local_llm_server.rrg5_load_probe import classify_pair_load_failure


def test_classifies_startup_exit_without_retaining_raw_private_text() -> None:
    result = classify_pair_load_failure(
        RuntimeError(
            "llama-server exited during startup with code 1. failed at /Users/alice/model.gguf"
        )
    )

    assert result == {
        "category": "backend_startup_exit",
        "error_type": "RuntimeError",
        "startup_exit_code": 1,
        "raw_error_retained": False,
    }
    assert "alice" not in str(result)
    assert "model.gguf" not in str(result)


def test_classifies_port_bind_before_generic_startup_exit() -> None:
    result = classify_pair_load_failure(
        RuntimeError(
            "llama-server exited during startup with code 1. error: address already in use"
        )
    )

    assert result["category"] == "port_bind"
    assert result["startup_exit_code"] == 1


def test_classifies_memory_allocation_before_generic_startup_exit() -> None:
    result = classify_pair_load_failure(
        RuntimeError(
            "llama-server exited during startup with code 1. ggml: failed to allocate buffer"
        )
    )

    assert result["category"] == "memory_allocation"


def test_classifies_model_load_before_generic_startup_exit() -> None:
    result = classify_pair_load_failure(
        RuntimeError(
            "llama-server exited during startup with code 1. error loading model"
        )
    )

    assert result["category"] == "model_load"


def test_classifies_runtime_cli_incompatibility() -> None:
    result = classify_pair_load_failure(
        RuntimeError("llama-server exited during startup with code 1. unknown argument: --fit")
    )

    assert result["category"] == "runtime_cli_incompatibility"


def test_classifies_startup_timeout() -> None:
    result = classify_pair_load_failure(
        TimeoutError("llama-server did not become ready within 60s")
    )

    assert result["category"] == "startup_timeout"
    assert result["startup_exit_code"] is None
