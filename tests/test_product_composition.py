from __future__ import annotations

from pathlib import Path

from local_llm_server.product_composition import install_product_http_stack
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.scheduler_policy import RequestSchedulerSettings
from local_llm_server.server import ServerSettings, create_app


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _app():
    manager = ModelRuntimeManager(default_model="demo")
    manager.add(
        {
            "model": "demo",
            "model_id": "org/demo",
            "backend": "fake",
            "modalities": ["text"],
            "max_concurrent_requests": 1,
        },
        _Engine(),
    )
    return create_app(manager, settings=ServerSettings(enable_admin_api=False))


def test_product_http_stack_installs_scheduler_policy_completion_stream_metrics_and_product_api_once(tmp_path):
    app = _app()
    settings = RequestSchedulerSettings(queue_capacity=2)

    install_product_http_stack(
        app,
        evaluation_root=tmp_path / "evaluations",
        scheduler_settings=settings,
    )
    install_product_http_stack(
        app,
        evaluation_root=tmp_path / "evaluations",
        scheduler_settings=settings,
    )

    assert app.state.request_resource_admission_installed is True
    assert app.state.request_scheduler_installed is True
    assert app.state.request_scheduler_settings == settings
    assert app.state.runtime_gate_registry is not None
    assert app.state.canonical_request_policy_installed is True
    assert app.state.completion_metrics_installed is True
    assert app.state.streaming_metrics_installed is True
    assert app.state.product_api_installed is True
    route_paths = [
        path
        for route in app.routes
        if (path := getattr(route, "path", None)) is not None
    ]
    assert route_paths.count("/v1/audio/transcriptions") == 1


def test_product_http_stack_keeps_resource_admission_when_queue_is_unconfigured(tmp_path):
    app = _app()
    install_product_http_stack(
        app,
        evaluation_root=tmp_path / "evaluations",
        scheduler_settings=RequestSchedulerSettings(),
    )
    assert app.state.request_resource_admission_installed is True
    assert app.state.request_scheduler_installed is True
    assert app.state.request_scheduler_settings.enabled is False
    assert app.state.runtime_gate_registry is None
    assert app.state.completion_metrics_installed is True


def test_supported_server_entrypoints_use_shared_product_composition():
    package_root = Path(__file__).resolve().parents[1] / "src" / "local_llm_server"
    public_api = (package_root / "__init__.py").read_text(encoding="utf-8")
    policy_server = (package_root / "policy_server.py").read_text(encoding="utf-8")

    assert "from .product_composition import install_product_http_stack" in public_api
    assert "install_product_http_stack(application)" in public_api
    assert "from .product_composition import install_product_http_stack" in policy_server
    assert "install_product_http_stack(application)" in policy_server
