"""Validated local custom evaluation test sets.

Uploaded files describe data only. They cannot provide Python scorers, templates
or executable code; scoring is restricted to deterministic checks already
implemented by the repository.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from .core.contracts import TaskType
from .evaluation import EvaluationSample, TestSet

_SCHEMA_VERSION = 1
_MAX_SAMPLES = 10_000
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_ALLOWED_TASKS = {TaskType.CHAT, TaskType.STRUCTURED_GENERATION}
_ALLOWED_EXPECTATIONS = {
    "exact",
    "exact_ci",
    "contains",
    "word_count",
    "comma_count",
    "json",
}


class CustomTestSetStore:
    def __init__(self, root: Path, *, reserved_ids: set[str] | None = None) -> None:
        self.root = root.expanduser()
        self.reserved_ids = set(reserved_ids or ())

    def save(self, test_set: TestSet, *, replace: bool = False) -> Path:
        if test_set.test_set_id in self.reserved_ids:
            raise ValueError(f"test-set id is reserved: {test_set.test_set_id}")
        _validate_identifier(test_set.test_set_id, "id")
        _validate_identifier(test_set.version, "version")
        self.root.mkdir(parents=True, exist_ok=True)
        target = self._path(test_set.test_set_id, test_set.version)
        if target.exists() and not replace:
            raise FileExistsError(
                f"test set already exists: {test_set.test_set_id}@{test_set.version}"
            )
        temp = target.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(test_set_to_upload_dict(test_set), sort_keys=True, indent=2),
            encoding="utf-8",
        )
        os.replace(temp, target)
        return target

    def list_test_sets(self) -> tuple[TestSet, ...]:
        if not self.root.exists():
            return ()
        result: list[TestSet] = []
        for path in self.root.glob("*.json"):
            if not path.is_file():
                continue
            try:
                result.append(parse_test_set_payload(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, ValueError, json.JSONDecodeError, TypeError):
                continue
        return tuple(sorted(result, key=lambda item: (item.test_set_id, item.version)))

    def resolve(self, test_set_id: str, version: str | None = None) -> TestSet | None:
        matches = [
            item
            for item in self.list_test_sets()
            if item.test_set_id == test_set_id and (version is None or item.version == version)
        ]
        if not matches:
            return None
        if version is None and len(matches) > 1:
            raise ValueError(
                f"multiple versions exist for {test_set_id}; test_set_version is required"
            )
        return matches[0]

    def _path(self, test_set_id: str, version: str) -> Path:
        _validate_identifier(test_set_id, "id")
        _validate_identifier(version, "version")
        path = (self.root / f"{test_set_id}@{version}.json").resolve()
        if path.parent != self.root.resolve():
            raise ValueError("invalid custom test-set path")
        return path


def parse_test_set_bytes(raw: bytes) -> TestSet:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("test-set file must be UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid test-set JSON: {exc.msg}") from exc
    return parse_test_set_payload(payload)


def parse_test_set_payload(payload: Any) -> TestSet:
    if not isinstance(payload, Mapping):
        raise ValueError("test-set root must be a JSON object")
    if payload.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {_SCHEMA_VERSION}")

    test_set_id = _required_identifier(payload.get("id"), "id")
    version = _required_identifier(payload.get("version"), "version")
    samples_value = payload.get("samples")
    if not isinstance(samples_value, list):
        raise ValueError("samples must be an array")
    if len(samples_value) < 10:
        raise ValueError("custom test set must contain at least 10 samples")
    if len(samples_value) > _MAX_SAMPLES:
        raise ValueError(f"custom test set cannot exceed {_MAX_SAMPLES} samples")

    provenance_value = payload.get("provenance", {})
    if not isinstance(provenance_value, Mapping):
        raise ValueError("provenance must be an object")
    _ensure_json_value(provenance_value, "provenance")
    provenance = {
        "source": "user-upload",
        "schema_version": _SCHEMA_VERSION,
        "declared": dict(provenance_value),
        "scoring": "deterministic-objective",
    }

    samples = tuple(
        _parse_sample(sample, index=index)
        for index, sample in enumerate(samples_value)
    )
    return TestSet(
        test_set_id=test_set_id,
        version=version,
        samples=samples,
        provenance=provenance,
    )


def test_set_to_upload_dict(test_set: TestSet) -> dict[str, object]:
    declared = test_set.provenance.get("declared", {})
    return {
        "schema_version": _SCHEMA_VERSION,
        "id": test_set.test_set_id,
        "version": test_set.version,
        "provenance": dict(declared) if isinstance(declared, Mapping) else {},
        "samples": [
            {
                "id": sample.sample_id,
                "task": sample.task.value,
                "input": sample.payload.get("input"),
                "expected": dict(sample.expected),
                "tags": list(sample.tags),
            }
            for sample in sorted(test_set.samples, key=lambda item: item.sample_id)
        ],
    }


def _parse_sample(value: Any, *, index: int) -> EvaluationSample:
    if not isinstance(value, Mapping):
        raise ValueError(f"samples[{index}] must be an object")
    sample_id = _required_identifier(value.get("id"), f"samples[{index}].id")
    task_raw = value.get("task", TaskType.CHAT.value)
    try:
        task = TaskType(str(task_raw))
    except ValueError as exc:
        raise ValueError(f"samples[{index}].task is unsupported: {task_raw}") from exc
    if task not in _ALLOWED_TASKS:
        raise ValueError(
            f"samples[{index}].task must be chat or structured_generation"
        )

    input_text = value.get("input")
    if not isinstance(input_text, str) or not input_text.strip():
        raise ValueError(f"samples[{index}].input must be a non-empty string")

    expected_value = value.get("expected")
    if not isinstance(expected_value, Mapping) or not expected_value:
        raise ValueError(f"samples[{index}].expected must be a non-empty object")
    unknown = set(expected_value) - _ALLOWED_EXPECTATIONS
    if unknown:
        raise ValueError(
            f"samples[{index}].expected contains unsupported checks: {', '.join(sorted(unknown))}"
        )
    expected = dict(expected_value)
    _validate_expectations(expected, index=index)

    tags_value = value.get("tags", [])
    if not isinstance(tags_value, list) or not all(
        isinstance(tag, str) and tag.strip() for tag in tags_value
    ):
        raise ValueError(f"samples[{index}].tags must be an array of non-empty strings")

    return EvaluationSample(
        sample_id=sample_id,
        task=task,
        payload={"input": input_text},
        expected=expected,
        tags=tuple(tags_value),
    )


def _validate_expectations(expected: dict[str, Any], *, index: int) -> None:
    for key in ("word_count", "comma_count"):
        if key in expected:
            value = expected[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"samples[{index}].expected.{key} must be an integer >= 0")
    if "contains" in expected:
        value = expected["contains"]
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ValueError(
                f"samples[{index}].expected.contains must be a non-empty string array"
            )
    for key in ("exact", "exact_ci"):
        if key in expected and isinstance(expected[key], (dict, list)):
            raise ValueError(
                f"samples[{index}].expected.{key} must be a scalar JSON value"
            )
    _ensure_json_value(expected, f"samples[{index}].expected")


def _required_identifier(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    text = value.strip()
    _validate_identifier(text, name)
    return text


def _validate_identifier(value: str, name: str) -> None:
    if not _ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"{name} must match {_ID_PATTERN.pattern}"
        )


def _ensure_json_value(value: Any, name: str) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain valid finite JSON values") from exc
