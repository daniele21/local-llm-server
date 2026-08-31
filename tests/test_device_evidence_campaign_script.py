from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_device_evidence_campaign.py"
_SPEC = importlib.util.spec_from_file_location("run_device_evidence_campaign", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
campaign_script = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(campaign_script)


def _args(*, scope: str = "full", backend: str | None = "llama_server") -> SimpleNamespace:
    return SimpleNamespace(scope=scope, multi_model_backend=backend)


def test_rrg5_backend_preflight_refuses_incompatible_llama_server(monkeypatch) -> None:
    monkeypatch.setattr(
        campaign_script,
        "resolve_llama_server_binary",
        lambda _cfg: (_ for _ in ()).throw(
            RuntimeError("incompatible binary at /private/path/llama-server")
        ),
    )

    result = campaign_script._rrg5_backend_preflight(_args())

    assert result is not None
    assert result["status"] == "INCONCLUSIVE"
    assert result["checks"]["ready"] is False
    assert result["checks"]["backend_version"] is None
    assert "/private/" not in str(result)


def test_rrg5_backend_preflight_records_public_compatible_identity(monkeypatch) -> None:
    compatibility = SimpleNamespace(
        backend_version="build-10621@c1d0e7a",
        profile="validated-v0.3.0",
    )
    monkeypatch.setattr(
        campaign_script,
        "resolve_llama_server_binary",
        lambda _cfg: (Path("/private/llama-server"), compatibility),
    )

    result = campaign_script._rrg5_backend_preflight(_args())

    assert result is not None
    assert result["status"] == "PASS"
    assert result["checks"]["ready"] is True
    assert result["checks"]["backend_version"] == "build-10621@c1d0e7a"
    assert result["checks"]["profile"] == "validated-v0.3.0"
    assert "/private/" not in str(result)


def test_rrg5_backend_preflight_does_not_affect_minimum_l2_scope(monkeypatch) -> None:
    monkeypatch.setattr(
        campaign_script,
        "resolve_llama_server_binary",
        lambda _cfg: (_ for _ in ()).throw(AssertionError("must not probe")),
    )

    assert campaign_script._rrg5_backend_preflight(
        _args(scope="minimum-l2", backend="llama_server")
    ) is None
    assert campaign_script._rrg5_backend_preflight(
        _args(scope="full", backend="llama_cpp")
    ) is None
