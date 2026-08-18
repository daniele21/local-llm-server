from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_repository_l2_evidence_bridge_contract_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    process = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_l2_evidence_bridge.py")],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
