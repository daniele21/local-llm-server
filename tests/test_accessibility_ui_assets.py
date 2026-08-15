from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


STATIC = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "static"


def test_shell_implements_roving_tab_keyboard_semantics():
    script = (STATIC / "control-plane-shell.js").read_text(encoding="utf-8")

    assert "setAttribute('role', 'tablist')" in script
    assert "setAttribute('role', 'tab')" in script
    assert "setAttribute('role', 'tabpanel')" in script
    assert "aria-controls" in script
    assert "aria-selected" in script
    assert "aria-labelledby" in script
    assert "button.tabIndex = active ? 0 : -1" in script
    for key in ("ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End"):
        assert key in script


def test_shell_has_keyboard_skip_navigation_and_hidden_panel_state():
    script = (STATIC / "control-plane-shell.js").read_text(encoding="utf-8")

    assert "Skip to main content" in script
    assert "[data-control-plane-skip-link]" in script
    assert "dataset.controlPlaneSkipLink" in script
    assert "main.tabIndex = -1" in script
    assert "panel.hidden = !active" in script
    assert "aria-hidden" in script
    assert "focusable', 'false'" in script


def test_design_system_has_visible_focus_for_native_and_control_plane_controls():
    css = (STATIC / "design-system.css").read_text(encoding="utf-8")

    for selector in (
        "button:focus-visible",
        "a:focus-visible",
        "input:focus-visible",
        "textarea:focus-visible",
        "select:focus-visible",
        ".nav-item:focus-visible",
    ):
        assert selector in css
    assert "outline: 3px solid var(--ds-focus)" in css
    assert ".ds-skip-link:focus" in css


def test_status_component_has_visible_text_plus_non_textual_indicator_contract():
    css = (STATIC / "design-system.css").read_text(encoding="utf-8")

    assert ".ds-status::before" in css
    assert ".ds-status[data-status=\"ready\"]" in css
    assert "color: var(--ds-text)" in css
    # The pseudo-element is supplementary; status labels stay in DOM text in
    # source-backed renderers rather than relying on a color-only class.
    shell = (STATIC / "control-plane-shell.js").read_text(encoding="utf-8")
    assert 'data-status="loading">Loading sources</span>' in shell


def test_control_plane_layouts_collapse_and_preserve_horizontal_table_access():
    shell_css = (STATIC / "control-plane-shell.css").read_text(encoding="utf-8")
    design_css = (STATIC / "design-system.css").read_text(encoding="utf-8")

    assert "@media (max-width: 1100px)" in shell_css
    assert "@media (max-width: 720px)" in shell_css
    assert "@media (max-width: 420px)" in shell_css
    assert "grid-template-columns: 1fr" in shell_css
    assert "min-width: 0" in shell_css
    assert "overflow-wrap: anywhere" in shell_css
    assert ".ds-table-wrap" in design_css
    assert "overflow-x: auto" in design_css
    assert "scrollbar-gutter: stable" in design_css


def test_reduced_motion_contract_is_global_for_control_plane_motion():
    css = (STATIC / "design-system.css").read_text(encoding="utf-8")
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "scroll-behavior: auto !important" in css
    assert "transition: none" in css


def test_control_plane_shell_javascript_is_syntactically_valid_when_node_is_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed in this test environment")
    completed = subprocess.run(
        [node, "--check", str(STATIC / "control-plane-shell.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
