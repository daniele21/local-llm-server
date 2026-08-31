from pathlib import Path

from scripts.verify_change_review import validate_change_review


def test_repository_change_review_policy_passes() -> None:
    assert validate_change_review(Path(".")) == []
