from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _run(relative: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / relative)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_upstream_product_experience_contract_passes_for_adopted_profile():
    result = _run("scripts/verify_product_experience.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout


def test_local_product_ui_l2_fitness_contract_passes_current_repository():
    result = _run("scripts/verify_product_ui_l2.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULT: PASS" in result.stdout
    assert "manual_accessibility_status remains pending" in result.stdout
    assert "representative_user_usability_status remains pending" in result.stdout
