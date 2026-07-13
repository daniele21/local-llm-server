from __future__ import annotations

import subprocess
import sys

from local_llm_server.server import app


def test_package_import_has_no_global_stream_logging_or_signal_side_effects():
    code = """
import logging
import signal
import sys

stdout = sys.stdout
stderr = sys.stderr
handlers = tuple(logging.getLogger().handlers)
signals = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}

import local_llm_server
import local_llm_server.engine

assert sys.stdout is stdout
assert sys.stderr is stderr
assert tuple(logging.getLogger().handlers) == handlers
assert {sig: signal.getsignal(sig) for sig in signals} == signals
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_terminal_endpoint_is_not_registered():
    assert "/api/v1/terminal/run" not in {route.path for route in app.routes}
