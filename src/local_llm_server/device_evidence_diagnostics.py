"""Bounded post-run diagnostics for representative device campaigns.

The diagnostics explain already-produced evidence without changing any evidence
threshold, runtime behavior, or acceptance verdict. Returned messages are built
from bounded reviewer/comparison fields and never include prompts, outputs,
private model paths, or process identifiers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .evaluation_history import compare_run_summaries, summarize_report_payload


def _load_object(path: Path) -> Mapping[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def campaign_diagnostics(output_dir: Path) -> tuple[str, ...]:
    """Return concise, public-safe explanations for non-PASS campaign phases."""
    root = output_dir.expanduser()
    summary = _load_object(root / "campaign-summary.json") or {}
    phases = summary.get("phases") if isinstance(summary.get("phases"), Mapping) else {}
    messages: list[str] = []

    evaluation = phases.get("evaluation_ev_3") if isinstance(phases, Mapping) else None
    if isinstance(evaluation, Mapping) and evaluation.get("status") != "PASS":
        messages.extend(_evaluation_diagnostics(root))

    bundle = phases.get("validate_minimum_l2_bundle") if isinstance(phases, Mapping) else None
    if isinstance(bundle, Mapping) and bundle.get("status") != "PASS":
        payload = _load_object(root / "l2-device-bundle-summary.json")
        if payload is not None:
            errors = payload.get("errors")
            if isinstance(errors, list):
                messages.extend(
                    f"L2 bundle: {item}" for item in errors if isinstance(item, str) and item
                )

    rrg5 = phases.get("multimodel_rrg_5") if isinstance(phases, Mapping) else None
    if isinstance(rrg5, Mapping) and rrg5.get("status") != "PASS":
        review = _load_object(root / "multimodel-review.json")
        if review is not None:
            state = review.get("state")
            if isinstance(state, str):
                messages.append(f"RRG-5 review state: {state}")
            reasons = review.get("reasons")
            if isinstance(reasons, list):
                messages.extend(
                    f"RRG-5: {item}" for item in reasons if isinstance(item, str) and item
                )
        else:
            checks = rrg5.get("checks")
            if isinstance(checks, Mapping):
                if checks.get("host_safety_refused") is True:
                    messages.append("RRG-5: host-memory safety gate refused execution")
                elif checks.get("precondition_refused") is True:
                    messages.append("RRG-5: one or more attributable execution preconditions were unavailable")

    return tuple(dict.fromkeys(messages))


def _evaluation_diagnostics(root: Path) -> list[str]:
    first = _load_object(root / "evaluation-off-a.json")
    second = _load_object(root / "evaluation-off-b.json")
    if first is None or second is None:
        return ["EV-3: one or both evaluation reports are missing or invalid JSON"]

    messages: list[str] = []
    if first.get("complete") is not True:
        messages.append("EV-3: run A is incomplete")
    if second.get("complete") is not True:
        messages.append("EV-3: run B is incomplete")
    try:
        a = summarize_report_payload(first)
        b = summarize_report_payload(second)
    except ValueError as exc:
        return messages + [f"EV-3: {exc}"]

    if a.sample_count != 10 or b.sample_count != 10:
        messages.append(
            f"EV-3: expected 10 samples per run, observed {a.sample_count} and {b.sample_count}"
        )
    comparison = compare_run_summaries(a, b)
    messages.extend(f"EV-3: {reason}" for reason in comparison.reasons)
    if not comparison.reasons:
        if not comparison.comparable:
            messages.append("EV-3: runs are not comparable")
        elif not comparison.evidence_grade:
            messages.append("EV-3: comparison is not evidence-grade")
        elif not comparison.attribution_safe:
            messages.append("EV-3: comparison is not attribution-safe")
    return messages


def print_campaign_diagnostics(output_dir: Path) -> None:
    messages = campaign_diagnostics(output_dir)
    if not messages:
        return
    print("\nDiagnostic explanation")
    print("=" * 22)
    for message in messages:
        print(f"- {message}")
