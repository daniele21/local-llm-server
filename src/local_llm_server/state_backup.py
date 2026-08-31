"""Bounded export/restore for small server-owned JSON state.

This module deliberately excludes model weights, model/download caches, logs,
build artifacts and arbitrary filesystem paths. The archive is a portable JSON
envelope with category-specific validation and checksums.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping

from .artifact_identity import ArtifactVerificationReceipt
from .artifact_verification import default_receipt_dir
from .evaluation_history import summarize_report_payload
from .evaluation_testsets import parse_test_set_payload

_ARCHIVE_SCHEMA_VERSION = 1
_MAX_FILES_PER_CATEGORY = 10_000
_MAX_ENTRY_BYTES = 128 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
_SAFE_JSON_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9@._-]{0,199}\.json$")
_CATEGORIES = (
    "evaluation_reports",
    "custom_test_sets",
    "artifact_verification_receipts",
)


def default_evaluation_dir() -> Path:
    configured = os.getenv("LOCAL_LLM_EVALUATION_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local-llm-server" / "evaluations"


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size > _MAX_ENTRY_BYTES:
        raise ValueError(f"state file exceeds {_MAX_ENTRY_BYTES} bytes: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"state file must contain a JSON object: {path.name}")
    return payload


def _validate_evaluation_report(name: str, payload: Mapping[str, Any]) -> None:
    schema = payload.get("schema_version", 0)
    if schema not in {0, 1}:
        raise ValueError(f"unsupported evaluation report schema_version: {schema}")
    # schema v0 is the pre-L1 persisted report shape. v1 reserves an explicit
    # version while keeping the report body backward compatible.
    summary = summarize_report_payload(payload)
    if not summary.run_id:
        raise ValueError("evaluation report run_id is missing")
    if name != f"{summary.run_id}.json":
        raise ValueError("evaluation report filename does not match manifest.run_id")


def _validate_test_set(name: str, payload: Mapping[str, Any]) -> None:
    test_set = parse_test_set_payload(payload)
    if name != f"{test_set.test_set_id}@{test_set.version}.json":
        raise ValueError("custom test-set filename does not match id/version")


def _decode_receipt(payload: Mapping[str, Any]) -> ArtifactVerificationReceipt:
    schema = payload.get("schema_version")
    if schema is None:
        body: Mapping[str, Any] = payload
    elif schema == 1:
        raw = payload.get("receipt")
        if not isinstance(raw, Mapping):
            raise ValueError("artifact receipt schema v1 requires receipt object")
        body = raw
    else:
        raise ValueError(f"unsupported artifact receipt schema_version: {schema}")
    return ArtifactVerificationReceipt.from_private_payload(body)


def _validate_receipt(_name: str, payload: Mapping[str, Any]) -> None:
    receipt = _decode_receipt(payload)
    if not receipt.logical_id or len(receipt.sha256) != 64:
        raise ValueError("artifact verification receipt identity is incomplete")


_VALIDATORS: dict[str, Callable[[str, Mapping[str, Any]], None]] = {
    "evaluation_reports": _validate_evaluation_report,
    "custom_test_sets": _validate_test_set,
    "artifact_verification_receipts": _validate_receipt,
}


def _category_paths(evaluation_root: Path, receipt_root: Path) -> dict[str, Path]:
    return {
        "evaluation_reports": evaluation_root,
        "custom_test_sets": evaluation_root / "test_sets",
        "artifact_verification_receipts": receipt_root,
    }


def _collect_category(category: str, root: Path) -> list[dict[str, object]]:
    if not root.exists():
        return []
    paths = sorted(path for path in root.glob("*.json") if path.is_file())
    if len(paths) > _MAX_FILES_PER_CATEGORY:
        raise ValueError(f"{category} exceeds {_MAX_FILES_PER_CATEGORY} files")
    entries: list[dict[str, object]] = []
    for path in paths:
        if not _SAFE_JSON_NAME.fullmatch(path.name):
            raise ValueError(f"unsafe owned state filename: {path.name}")
        payload = _read_json_object(path)
        _VALIDATORS[category](path.name, payload)
        entries.append(
            {
                "name": path.name,
                "sha256": _sha256(payload),
                "payload": payload,
            }
        )
    return entries


def build_archive(*, evaluation_root: Path, receipt_root: Path) -> dict[str, object]:
    roots = _category_paths(evaluation_root.expanduser(), receipt_root.expanduser())
    return {
        "schema_version": _ARCHIVE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "categories": {
            category: _collect_category(category, roots[category])
            for category in _CATEGORIES
        },
    }


def validate_archive(payload: object) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    if not isinstance(payload, Mapping):
        raise ValueError("state archive root must be an object")
    if payload.get("schema_version") != _ARCHIVE_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported state archive schema_version: {payload.get('schema_version')}"
        )
    categories = payload.get("categories")
    if not isinstance(categories, Mapping):
        raise ValueError("state archive categories must be an object")
    unknown = set(categories) - set(_CATEGORIES)
    missing = set(_CATEGORIES) - set(categories)
    if unknown or missing:
        raise ValueError(
            f"state archive categories mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )

    validated: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    total_bytes = 0
    for category in _CATEGORIES:
        raw_entries = categories.get(category)
        if not isinstance(raw_entries, list):
            raise ValueError(f"{category} must be an array")
        if len(raw_entries) > _MAX_FILES_PER_CATEGORY:
            raise ValueError(f"{category} exceeds {_MAX_FILES_PER_CATEGORY} files")
        seen: set[str] = set()
        items: list[tuple[str, dict[str, Any]]] = []
        for raw in raw_entries:
            if not isinstance(raw, Mapping):
                raise ValueError(f"{category} entry must be an object")
            name = raw.get("name")
            digest = raw.get("sha256")
            entry_payload = raw.get("payload")
            if not isinstance(name, str) or not _SAFE_JSON_NAME.fullmatch(name):
                raise ValueError(f"unsafe {category} filename")
            if name in seen:
                raise ValueError(f"duplicate {category} filename: {name}")
            seen.add(name)
            if not isinstance(entry_payload, dict):
                raise ValueError(f"{category}/{name} payload must be an object")
            encoded = _canonical_bytes(entry_payload)
            total_bytes += len(encoded)
            if len(encoded) > _MAX_ENTRY_BYTES or total_bytes > _MAX_ARCHIVE_BYTES:
                raise ValueError("state archive exceeds bounded size limits")
            if not isinstance(digest, str) or digest != hashlib.sha256(encoded).hexdigest():
                raise ValueError(f"checksum mismatch for {category}/{name}")
            _VALIDATORS[category](name, entry_payload)
            items.append((name, entry_payload))
        validated[category] = items
    return validated


def export_state(output: Path, *, evaluation_root: Path, receipt_root: Path) -> Path:
    archive = build_archive(evaluation_root=evaluation_root, receipt_root=receipt_root)
    encoded = json.dumps(archive, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if len(encoded.encode("utf-8")) > _MAX_ARCHIVE_BYTES:
        raise ValueError("state archive exceeds bounded size limit")
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    temp.write_text(encoded, encoding="utf-8")
    os.replace(temp, output)
    return output


def restore_state(
    archive_path: Path,
    *,
    evaluation_root: Path,
    receipt_root: Path,
    replace: bool = False,
) -> dict[str, int]:
    archive_path = archive_path.expanduser()
    if archive_path.stat().st_size > _MAX_ARCHIVE_BYTES:
        raise ValueError("state archive exceeds bounded size limit")
    payload = json.loads(archive_path.read_text(encoding="utf-8"))
    # Full validation is deliberately complete before any directory creation or write.
    validated = validate_archive(payload)
    roots = _category_paths(evaluation_root.expanduser(), receipt_root.expanduser())

    targets: list[tuple[str, Path, dict[str, Any]]] = []
    for category, items in validated.items():
        root = roots[category].resolve()
        for name, item in items:
            target = (root / name).resolve()
            if target.parent != root:
                raise ValueError(f"restore target escapes owned root: {category}/{name}")
            if target.exists() and not replace:
                raise FileExistsError(f"restore target already exists: {category}/{name}")
            targets.append((category, target, item))

    for _category, target, _item in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []
    try:
        for _category, target, item in targets:
            temp = target.with_suffix(target.suffix + ".restore-tmp")
            temp.write_bytes(_canonical_bytes(item))
            staged.append((temp, target))
        for temp, target in staged:
            os.replace(temp, target)
    finally:
        for temp, _target in staged:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
    return {category: len(validated[category]) for category in _CATEGORIES}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m local_llm_server.state_backup")
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export", help="Export bounded server-owned JSON state.")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--evaluation-dir", type=Path, default=default_evaluation_dir())
    export.add_argument("--verification-dir", type=Path, default=default_receipt_dir())
    restore = sub.add_parser("restore", help="Validate and restore bounded server-owned JSON state.")
    restore.add_argument("--input", type=Path, required=True)
    restore.add_argument("--evaluation-dir", type=Path, default=default_evaluation_dir())
    restore.add_argument("--verification-dir", type=Path, default=default_receipt_dir())
    restore.add_argument("--replace", action="store_true", default=False)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "export":
        path = export_state(
            args.output,
            evaluation_root=args.evaluation_dir,
            receipt_root=args.verification_dir,
        )
        print(f"Exported server-owned state to {path}")
        return 0
    counts = restore_state(
        args.input,
        evaluation_root=args.evaluation_dir,
        receipt_root=args.verification_dir,
        replace=args.replace,
    )
    print("Restored server-owned state: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
