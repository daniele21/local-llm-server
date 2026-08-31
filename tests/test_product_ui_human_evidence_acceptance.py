from __future__ import annotations

import json
from pathlib import Path

from local_llm_server.l2_evidence_bridge import validate_product_ui_evidence


ROOT = Path(__file__).resolve().parents[1]
ACCESSIBILITY = ROOT / "docs" / "evidence" / "manual-accessibility-2026-08-31.json"
USABILITY = ROOT / "docs" / "evidence" / "representative-usability-2026-08-31.json"
SUMMARY = ROOT / "docs" / "evidence" / "product-ui-evidence-summary-2026-08-31.json"
POLICY = ROOT / ".engineering" / "product-ui-l2.json"
BASELINE = ROOT / ".engineering" / "baseline.json"
EXPECTED_SOURCE = "a29e77c1ce4e65294440cfe4fc47e33c92173096"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_retained_product_ui_human_evidence_is_acceptance_ready() -> None:
    accessibility = _load(ACCESSIBILITY)
    usability = _load(USABILITY)

    result = validate_product_ui_evidence(
        accessibility=accessibility,
        usability=usability,
    )

    assert accessibility["source_revision"] == EXPECTED_SOURCE
    assert usability["source_revision"] == EXPECTED_SOURCE
    assert result["errors"] == []
    assert result["manual_accessibility"] == {
        "evidence_present": True,
        "acceptance_ready": True,
        "blocking_findings": 0,
    }
    assert result["representative_user_usability"] == {
        "evidence_present": True,
        "acceptance_ready": True,
        "blocking_findings": 0,
    }
    assert result["full_product_ui_evidence_ready"] is True


def test_promoted_statuses_match_retained_evidence() -> None:
    policy = _load(POLICY)
    baseline = _load(BASELINE)
    summary = _load(SUMMARY)

    manual = policy["manual_evidence"]
    assert manual["manual_accessibility_status"] == "complete"
    assert manual["representative_user_usability_status"] == "complete"
    assert manual["accepted_source_revision"] == EXPECTED_SOURCE
    assert manual["evidence_summary"] == "docs/evidence/product-ui-evidence-summary-2026-08-31.json"

    product_ui = baseline["adoption"]["product_ui_l2"]
    assert product_ui["manual_accessibility_evidence"] == "accepted-2026-08-31"
    assert product_ui["representative_user_usability_evidence"] == "accepted-2026-08-31"
    assert product_ui["evidence_summary"] == "docs/evidence/product-ui-evidence-summary-2026-08-31.json"

    assert summary["source_revision"] == EXPECTED_SOURCE
    assert summary["full_product_ui_evidence_ready"] is True
    assert summary["errors"] == []
