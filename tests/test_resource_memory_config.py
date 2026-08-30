from __future__ import annotations

import pytest

from local_llm_server.config import build_config


def test_explicit_memory_envelope_settings_are_resolved(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    cfg = build_config(
        model="nemotron-nano-4b-q8",
        resource_backend_overhead_bytes=100,
        resource_context_cache_bytes=200,
        resource_safety_margin_bytes=300,
        resource_request_estimate_bytes=400,
    )

    assert cfg["resource_backend_overhead_bytes"] == 100
    assert cfg["resource_context_cache_bytes"] == 200
    assert cfg["resource_safety_margin_bytes"] == 300
    assert cfg["resource_request_estimate_bytes"] == 400


def test_environment_memory_envelope_settings_are_resolved(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("LOCAL_LLM_RESOURCE_REQUEST_BASE_BYTES", "123")
    monkeypatch.setenv("LOCAL_LLM_RESOURCE_REQUEST_OUTPUT_TOKEN_BYTES", "7")

    cfg = build_config(model="nemotron-nano-4b-q8")

    assert cfg["resource_request_base_bytes"] == 123
    assert cfg["resource_request_output_token_bytes"] == 7


def test_explicit_memory_setting_precedes_environment(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setenv("LOCAL_LLM_RESOURCE_ESTIMATE_BYTES", "999")

    cfg = build_config(
        model="nemotron-nano-4b-q8",
        resource_estimate_bytes=321,
    )

    assert cfg["resource_estimate_bytes"] == 321


def test_negative_memory_envelope_setting_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    with pytest.raises(ValueError, match="resource_request_estimate_bytes"):
        build_config(
            model="nemotron-nano-4b-q8",
            resource_request_estimate_bytes=-1,
        )
