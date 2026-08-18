#!/usr/bin/env python3
"""Verify that L2 real-evidence bridge contracts cannot drift silently."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / ".engineering" / "l2-evidence-bridge.json"
PRODUCT_POLICY = ROOT / ".engineering" / "product-ui-l2.json"
MODULE = ROOT / "src" / "local_llm_server" / "l2_evidence_bridge.py"
RUNBOOK = ROOT / "docs" / "device-evidence-runbook.md"
ACCESSIBILITY_TEMPLATE = ROOT / "docs" / "evidence-templates" / "manual-accessibility.example.json"
USABILITY_TEMPLATE = ROOT / "docs" / "evidence-templates" / "representative-usability.example.json"


def _load(path: Path, errors: list[str]) -> dict:
    if not path.is_file():
        errors.append(f"missing required evidence bridge file: {path.relative_to(ROOT)}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"{path.relative_to(ROOT)} must contain a JSON object")
        return {}
    return payload


def main() -> int:
    errors: list[str] = []
    contract = _load(CONTRACT, errors)
    product = _load(PRODUCT_POLICY, errors)
    a11y_template = _load(ACCESSIBILITY_TEMPLATE, errors)
    usability_template = _load(USABILITY_TEMPLATE, errors)

    print("L2 real-evidence bridge contract")
    print(f"root: {ROOT}")

    if contract.get("schema_version") != 1:
        errors.append("l2-evidence-bridge.schema_version must be 1")

    hardware = contract.get("hardware_bundle")
    if not isinstance(hardware, dict):
        errors.append("hardware_bundle must be an object")
        hardware = {}
    required_files = hardware.get("required_files")
    expected_files = {
        "thinking-campaign.json",
        "evaluation-off-a.json",
        "evaluation-off-b.json",
        "reclamation-a.json",
        "reclamation-b.json",
        "reclamation-review.json",
        "resource-policy-smoke.json",
    }
    if not isinstance(required_files, list) or set(required_files) != expected_files:
        errors.append("hardware_bundle.required_files must match the canonical Wave D bundle")

    product_ui = contract.get("product_ui")
    if not isinstance(product_ui, dict):
        errors.append("product_ui must be an object")
        product_ui = {}
    research = product.get("privacy_research") if isinstance(product, dict) else None
    policy_fields = research.get("allowed_usability_fields") if isinstance(research, dict) else None
    bridge_fields = product_ui.get("usability_allowed_fields")
    if not isinstance(policy_fields, list) or not isinstance(bridge_fields, list):
        errors.append("product-ui usability allow-list must exist in both policy and bridge contract")
    elif policy_fields != bridge_fields:
        errors.append("product-ui usability allow-list drifted between product-ui-l2 and L2 evidence bridge")

    manual = product.get("manual_evidence") if isinstance(product, dict) else None
    if not isinstance(manual, dict):
        errors.append("product-ui manual_evidence contract is missing")
    else:
        for key in ("manual_accessibility_status", "representative_user_usability_status"):
            if manual.get(key) not in {"pending", "complete", "not-justified"}:
                errors.append(f"invalid product-ui manual evidence state: {key}")

    if a11y_template.get("evidence_kind") != "manual_accessibility":
        errors.append("manual accessibility template evidence_kind is invalid")
    if not str(a11y_template.get("study_id", "")).startswith("example-"):
        errors.append("manual accessibility template must be unmistakably non-evidence")
    if usability_template.get("evidence_kind") != "representative_user_usability":
        errors.append("representative usability template evidence_kind is invalid")
    records = usability_template.get("records")
    if not isinstance(records, list) or not records:
        errors.append("representative usability template must contain example records")
    else:
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"usability template record {index} must be an object")
                continue
            extra = sorted(set(record) - set(bridge_fields or []))
            if extra:
                errors.append(f"usability template record {index} contains non-allow-listed fields: {', '.join(extra)}")
            if not str(record.get("study_id", "")).startswith("example-"):
                errors.append(f"usability template record {index} must be unmistakably non-evidence")

    if not MODULE.is_file():
        errors.append("missing packaged L2 evidence bridge module")
    else:
        module_text = MODULE.read_text(encoding="utf-8")
        for marker in ("capture-thinking", "validate-hardware-bundle", "validate-product-ui"):
            if marker not in module_text:
                errors.append(f"L2 evidence bridge module missing command: {marker}")

    if not RUNBOOK.is_file():
        errors.append("missing representative device evidence runbook")
    else:
        runbook_text = RUNBOOK.read_text(encoding="utf-8")
        for marker in (
            "python -m local_llm_server.l2_evidence_bridge capture-thinking",
            "python -m local_llm_server.l2_evidence_bridge validate-hardware-bundle",
        ):
            if marker not in runbook_text:
                errors.append(f"device runbook missing evidence bridge procedure: {marker}")

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
