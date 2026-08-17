from __future__ import annotations

import signal

import uvicorn

from local_llm_server.policy_server import (
    _run_until_stopped,
    _shutdown_aware_server,
    browser_base_url,
)
from local_llm_server.server import create_app


def test_signal_notifies_application_before_uvicorn_marks_exit(monkeypatch):
    application = create_app()
    application.state.shutdown = False
    events: list[str] = []

    original_begin = __import__(
        "local_llm_server.server",
        fromlist=["begin_app_shutdown"],
    ).begin_app_shutdown

    def recording_begin(app):
        events.append("application")
        original_begin(app)

    def recording_super_exit(self, sig, frame):
        assert application.state.shutdown is True
        events.append("uvicorn")
        self.should_exit = True

    monkeypatch.setattr(
        "local_llm_server.server.begin_app_shutdown",
        recording_begin,
    )
    monkeypatch.setattr(uvicorn.Server, "handle_exit", recording_super_exit)

    config = uvicorn.Config(application, lifespan="off")
    server = _shutdown_aware_server(uvicorn, config, application)
    server.handle_exit(signal.SIGINT, None)

    assert events == ["application", "uvicorn"]
    assert application.state.shutdown is True
    assert server.should_exit is True


def test_browser_base_url_uses_loopback_for_wildcard_bind_addresses():
    assert browser_base_url("0.0.0.0", 1235) == "http://127.0.0.1:1235/"
    assert browser_base_url("::", 1235) == "http://127.0.0.1:1235/"


def test_browser_base_url_brackets_ipv6_addresses():
    assert browser_base_url("::1", 1235) == "http://[::1]:1235/"


def test_keyboard_interrupt_is_rendered_as_a_clean_server_stop(capsys):
    class InterruptedServer:
        def run(self):
            raise KeyboardInterrupt

    _run_until_stopped(InterruptedServer())

    assert "local-llm-server stopped" in capsys.readouterr().out


def test_shutdown_notification_is_idempotent_before_normal_finally_cleanup():
    application = create_app()
    config = uvicorn.Config(application, lifespan="off")
    server = _shutdown_aware_server(uvicorn, config, application)

    server.handle_exit(signal.SIGTERM, None)
    assert application.state.shutdown is True

    # run_server() calls begin_app_shutdown again from finally. Repeated
    # notification must remain harmless for long-lived response cleanup.
    from local_llm_server.server import begin_app_shutdown

    begin_app_shutdown(application)
    assert application.state.shutdown is True
