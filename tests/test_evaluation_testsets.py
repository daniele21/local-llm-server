from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_llm_server.evaluation_testsets import (
    CustomTestSetStore,
    parse_test_set_bytes,
    parse_test_set_payload,
)


def _payload(*, test_set_id="custom-general", version="1.0.0", count=10):
    return {
        "schema_version": 1,
        "id": test_set_id,
        "version": version,
        "provenance": {"owner": "local-test"},
        "samples": [
            {
                "id": f"sample-{index:02d}",
                "task": "chat",
                "input": f"Return only {index}",
                "expected": {"exact": str(index)},
                "tags": ["custom", "exact"],
            }
            for index in range(count)
        ],
    }


def test_uploaded_test_set_parses_to_deterministic_internal_contract():
    test_set = parse_test_set_bytes(json.dumps(_payload()).encode("utf-8"))

    assert test_set.test_set_id == "custom-general"
    assert test_set.version == "1.0.0"
    assert len(test_set.samples) == 10
    assert test_set.provenance["source"] == "user-upload"
    assert test_set.provenance["scoring"] == "deterministic-objective"
    assert test_set.samples[0].expected == {"exact": "0"}


def test_upload_rejects_executable_or_unsupported_scoring_shape():
    payload = _payload()
    payload["samples"][0]["expected"] = {"python": "import os; os.system('no')"}
    with pytest.raises(ValueError, match="unsupported checks"):
        parse_test_set_payload(payload)

    payload = _payload()
    payload["samples"][0]["task"] = "transcription"
    with pytest.raises(ValueError, match="chat or structured_generation"):
        parse_test_set_payload(payload)


def test_upload_requires_at_least_ten_samples_and_unique_ids():
    with pytest.raises(ValueError, match="at least 10"):
        parse_test_set_payload(_payload(count=9))

    payload = _payload()
    payload["samples"][1]["id"] = payload["samples"][0]["id"]
    with pytest.raises(ValueError, match="unique"):
        parse_test_set_payload(payload)


def test_upload_rejects_invalid_expectation_types_and_nonfinite_json():
    payload = _payload()
    payload["samples"][0]["expected"] = {"word_count": -1}
    with pytest.raises(ValueError, match="integer >= 0"):
        parse_test_set_payload(payload)

    payload = _payload()
    payload["samples"][0]["expected"] = {"contains": []}
    with pytest.raises(ValueError, match="non-empty string array"):
        parse_test_set_payload(payload)

    payload = _payload()
    payload["provenance"] = {"bad": float("nan")}
    with pytest.raises(ValueError, match="finite JSON"):
        parse_test_set_payload(payload)


def test_custom_store_persists_versions_atomically_and_requires_explicit_version_when_ambiguous(tmp_path: Path):
    store = CustomTestSetStore(tmp_path / "sets")
    v1 = parse_test_set_payload(_payload(version="1.0.0"))
    v2 = parse_test_set_payload(_payload(version="2.0.0"))

    first_path = store.save(v1)
    second_path = store.save(v2)

    assert first_path.is_file()
    assert second_path.is_file()
    assert {item.version for item in store.list_test_sets()} == {"1.0.0", "2.0.0"}
    assert store.resolve("custom-general", "1.0.0").identity == v1.identity
    with pytest.raises(ValueError, match="multiple versions"):
        store.resolve("custom-general")


def test_custom_store_rejects_collision_and_reserved_builtin_id(tmp_path: Path):
    store = CustomTestSetStore(tmp_path / "sets", reserved_ids={"general-purpose"})
    test_set = parse_test_set_payload(_payload())
    store.save(test_set)
    with pytest.raises(FileExistsError, match="already exists"):
        store.save(test_set)

    reserved = parse_test_set_payload(_payload(test_set_id="general-purpose"))
    with pytest.raises(ValueError, match="reserved"):
        store.save(reserved)


def test_custom_store_skips_corrupt_foreign_files_without_hiding_valid_sets(tmp_path: Path):
    store = CustomTestSetStore(tmp_path / "sets")
    valid = parse_test_set_payload(_payload())
    store.save(valid)
    (store.root / "broken.json").write_text("not json", encoding="utf-8")

    listed = store.list_test_sets()

    assert len(listed) == 1
    assert listed[0].identity == valid.identity
