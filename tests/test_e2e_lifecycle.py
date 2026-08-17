import json
from pathlib import Path
import shutil

import pytest

from tests.e2e.lifecycle import OWNER_FILE, OwnedRunState, stale_owned_roots


def test_owned_run_state_creates_isolated_evaluation_root_and_cleans_it():
    state = OwnedRunState.create()
    root = state.root
    try:
        assert state.evaluation_root.is_dir()
        assert state.owns_root() is True
        state.cleanup()
        assert not root.exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cleanup_refuses_root_when_ownership_marker_changes():
    state = OwnedRunState.create()
    root = state.root
    try:
        (root / OWNER_FILE).write_text(json.dumps({"run_id": "other"}), encoding="utf-8")
        assert state.owns_root() is False
        with pytest.raises(RuntimeError, match="unowned E2E root"):
            state.cleanup()
        assert root.exists()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_stale_owned_roots_reports_marked_run_state():
    state = OwnedRunState.create()
    try:
        assert state.root in stale_owned_roots()
    finally:
        state.cleanup()
