from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_llm_server.cli import _load_evidence_reports


def test_load_evidence_reports_preserves_json_objects_in_argument_order(tmp_path: Path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps({"schema_version": 1, "name": "first"}), encoding="utf-8")
    second.write_text(json.dumps({"schema_version": 1, "name": "second"}), encoding="utf-8")

    reports = _load_evidence_reports([first, second])

    assert reports == [
        {"schema_version": 1, "name": "first"},
        {"schema_version": 1, "name": "second"},
    ]


def test_load_evidence_reports_rejects_non_object_json(tmp_path: Path):
    path = tmp_path / "array.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        _load_evidence_reports([path])


def test_cli_exposes_review_thresholds_and_no_policy_mutation_action():
    cli_path = Path(__file__).resolve().parents[1] / "src" / "local_llm_server" / "cli.py"
    cli = cli_path.read_text(encoding="utf-8")

    assert '"evidence-review"' in cli
    assert "--min-reports" in cli
    assert "--min-complete-cycles" in cli
    assert "--allow-exploratory-identity" in cli
    assert "--allow-error-cycles" in cli
    assert "review_hardware_evidence" in cli
    assert "set_pinned" not in cli
    assert "select_eviction_candidates" not in cli
    assert "/api/v1/residency/evict" not in cli
