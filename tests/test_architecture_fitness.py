from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_architecture import validate_architecture


def test_repository_architecture_policy_passes() -> None:
    assert validate_architecture(Path(".")) == []


def test_architecture_policy_rejects_forbidden_import(tmp_path: Path) -> None:
    engineering = tmp_path / ".engineering"
    core = tmp_path / "src" / "local_llm_server" / "core"
    engineering.mkdir(parents=True)
    core.mkdir(parents=True)
    (core / "contracts.py").write_text("from fastapi import FastAPI\n", encoding="utf-8")

    policy = {
        "schema_version": 1,
        "source_root": "src/local_llm_server",
        "owners": [
            {"boundary": "backend_neutral_contracts", "path": "src/local_llm_server/core"}
        ],
        "rules": [
            {
                "id": "core-neutral",
                "paths": ["core/*.py"],
                "forbidden_import_prefixes": ["fastapi"],
                "rationale": "core stays transport-neutral",
            }
        ],
    }
    (engineering / "architecture-policy.json").write_text(json.dumps(policy), encoding="utf-8")

    errors = validate_architecture(tmp_path)
    assert any("imports fastapi" in error for error in errors)
