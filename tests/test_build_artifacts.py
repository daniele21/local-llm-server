from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from scripts import build_artifacts as ba


def _successful_build(root: Path, name: str) -> Path:
    build = root / name
    build.mkdir(parents=True)
    (build / ba.MANIFEST).write_text(json.dumps({"build_id": name}), encoding="utf-8")
    return build


def test_build_id_is_unique_even_for_same_timestamp():
    now = datetime(2026, 8, 17, 12, 0, tzinfo=timezone.utc)
    first = ba.new_build_id(now)
    second = ba.new_build_id(now)
    assert first.startswith("20260817T120000Z-")
    assert second.startswith("20260817T120000Z-")
    assert first != second


def test_promote_refuses_to_replace_successful_build(tmp_path: Path):
    final = tmp_path / "final"
    final.mkdir()
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "candidate").write_text("new", encoding="utf-8")

    with pytest.raises(FileExistsError):
        ba.promote(stage, final)

    assert stage.exists()
    assert (final / "candidate").exists() is False


def test_promote_moves_complete_stage_atomically_within_filesystem(tmp_path: Path):
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / ba.MANIFEST).write_text("{}", encoding="utf-8")
    final = tmp_path / "lineage" / "build-1"

    ba.promote(stage, final)

    assert not stage.exists()
    assert (final / ba.MANIFEST).is_file()


def test_retention_keeps_two_latest_successful_builds(tmp_path: Path):
    lineage = tmp_path / "lineage"
    _successful_build(lineage, "20260817T100000Z-a")
    _successful_build(lineage, "20260817T110000Z-b")
    _successful_build(lineage, "20260817T120000Z-c")

    ba.enforce_retention(lineage, keep=2)

    assert [path.name for path in ba.comparable_builds(lineage)] == [
        "20260817T110000Z-b",
        "20260817T120000Z-c",
    ]


def test_previous_manifest_ignores_incomplete_staging_directory(tmp_path: Path):
    lineage = tmp_path / "lineage"
    _successful_build(lineage, "20260817T100000Z-a")
    incomplete = lineage / "20260817T110000Z-b"
    incomplete.mkdir()

    previous = ba.previous_manifest(lineage)

    assert previous == {"build_id": "20260817T100000Z-a"}


def test_build_delta_records_required_dimensions():
    current = {
        "build_id": "new",
        "source": {"revision": "abc", "dirty": False},
        "dependencies": {"uv_lock_sha256": "1"},
        "toolchain": {"python": "3.11"},
        "lineage": {"channel": "local"},
        "artifacts": [{"name": "x.whl"}],
        "validation": ["wheel-content-check"],
    }
    previous = {
        "build_id": "old",
        "source": {"revision": "aaa", "dirty": False},
        "dependencies": {"uv_lock_sha256": "0"},
        "toolchain": {"python": "3.11"},
        "lineage": {"channel": "local"},
    }

    text = ba.build_delta(current, previous)

    for heading in (
        "## Source",
        "## Dependencies",
        "## Toolchain",
        "## Configuration",
        "## Compatibility / migrations",
        "## Artifact metrics",
        "## Validation",
    ):
        assert heading in text
