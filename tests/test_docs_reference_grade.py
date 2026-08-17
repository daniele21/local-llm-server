from datetime import date
from pathlib import Path

from scripts.verify_docs import _check_canonical_scopes, _check_freshness, validate_documents


def test_repository_documentation_policy_passes() -> None:
    errors, active_count = validate_documents(Path("."), today=date(2026, 8, 17))
    assert errors == []
    assert active_count == 2


def test_duplicate_canonical_scope_is_rejected(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "one.md").write_text("# One\nCanonical scope: same.fact\nSome durable body.\n", encoding="utf-8")
    (docs / "two.md").write_text("# Two\nCanonical scope: same.fact\nDifferent durable body.\n", encoding="utf-8")
    errors: list[str] = []
    _check_canonical_scopes(tmp_path, "Canonical scope:", errors)
    assert any("duplicate canonical scope" in error for error in errors)


def test_stale_review_date_is_rejected(tmp_path: Path) -> None:
    doc = tmp_path / "doc.md"
    doc.write_text("# Doc\nLast reviewed: 2025-01-01\n", encoding="utf-8")
    errors: list[str] = []
    _check_freshness(doc, "doc", 90, date(2026, 8, 17), errors)
    assert any("stale" in error for error in errors)
