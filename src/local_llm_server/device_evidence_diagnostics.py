"""Bounded post-run diagnostics for representative device campaigns.

The diagnostics explain already-produced evidence without changing any evidence
threshold, runtime behavior, or acceptance verdict. Returned messages are built
from bounded reviewer/comparison fields and never include prompts, outputs,
private model paths, or process identifiers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

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
        for suffix in ("a", "b"):
            report = _load_object(root / f"multimodel-{suffix}.json")
            if report is not None and report.get("complete") is not True:
                messages.extend(_rrg5_report_diagnostics(report, suffix.upper()))

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


def _rrg5_report_diagnostics(report: Mapping[str, Any], label: str) -> list[str]:
    messages: list[str] = []
    status = report.get("status")
    if isinstance(status, str):
        messages.append(f"RRG-5 report {label}: status={status}")

    cycles = report.get("cycles")
    if isinstance(cycles, list):
        for index, cycle in enumerate(cycles, start=1):
            if not isinstance(cycle, Mapping) or cycle.get("complete") is True:
                continue
            prefix = f"RRG-5 report {label} cycle {index}"
            failed_phase = cycle.get("failed_phase")
            error_type = cycle.get("error_type")
            if isinstance(failed_phase, str):
                detail = f" failed_phase={failed_phase}"
                if isinstance(error_type, str):
                    detail += f" error_type={error_type}"
                messages.append(prefix + detail)
                continue
            if cycle.get("runtime_identities_verified") is False:
                messages.append(prefix + ": runtime identities were not verified")
            if cycle.get("concurrent_transient_overlap_observed") is False:
                messages.append(prefix + ": concurrent transient accounting overlap was not observed")
            responses = cycle.get("responses")
            if isinstance(responses, list):
                statuses = [
                    item.get("http_status")
                    for item in responses
                    if isinstance(item, Mapping) and isinstance(item.get("http_status"), int)
                ]
                if statuses and any(value != 200 for value in statuses):
                    messages.append(prefix + f": inference HTTP statuses={statuses}")
            accounting = cycle.get("configured_accounting_after_unload")
            if isinstance(accounting, Mapping) and accounting.get("reservation_count") != 0:
                messages.append(prefix + ": accounting was not clean after unload")

    shutdown = report.get("shutdown_under_load")
    if isinstance(shutdown, Mapping) and shutdown.get("complete") is not True:
        prefix = f"RRG-5 report {label} shutdown-under-load"
        failed_phase = shutdown.get("failed_phase")
        error_type = shutdown.get("error_type")
        if isinstance(failed_phase, str):
            detail = f" failed_phase={failed_phase}"
            if isinstance(error_type, str):
                detail += f" error_type={error_type}"
            messages.append(prefix + detail)
        else:
            if shutdown.get("first_shutdown_reported_incomplete") is not True:
                messages.append(prefix + ": first bounded shutdown did not report incomplete")
            if shutdown.get("active_owner_retained_after_timeout") is not True:
                messages.append(prefix + ": active runtime ownership was not retained after timeout")
            final_accounting = shutdown.get("configured_accounting_after_retry")
            if isinstance(final_accounting, Mapping) and final_accounting.get("reservation_count") != 0:
                messages.append(prefix + ": accounting was not clean after retry")
    return messages


def print_campaign_diagnostics(output_dir: Path) -> None:
    messages = campaign_diagnostics(output_dir)
    if not messages:
        print("No non-PASS campaign diagnostics found.")
        return
    print("\nDiagnostic explanation")
    print("=" * 22)
    for message in messages:
        print(f"- {message}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explain bounded causes from an existing representative-device campaign."
    )
    parser.add_argument("directory", help="Existing campaign evidence directory.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    print_campaign_diagnostics(Path(args.directory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
