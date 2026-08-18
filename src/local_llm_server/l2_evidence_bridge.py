"""Privacy-safe bridge from real L2 evidence runs to deterministic acceptance review.

This module never manufactures device or human evidence. It can capture an explicit
thinking ON/OFF campaign without retaining prompt/output, validate the existing
representative-device evidence bundle, and validate bounded product-ui human evidence.
It deliberately does not mutate repository maturity/status files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .evaluation_history import compare_run_summaries, summarize_report_payload
from .hardware_evidence_review import EvidenceReviewSettings, review_hardware_evidence

_THINKING_PROMPT = "Reply with a concise explanation of why local inference can improve privacy."
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\\\")


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON evidence must contain an object: {path.name}")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    target = path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temp.replace(target)
    return target


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: Mapping[str, Any] | None = None,
    timeout: float = 300.0,
) -> tuple[int, Mapping[str, Any]]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback/user-selected endpoint
            status = int(getattr(response, "status", 200))
            raw = response.read()
    except HTTPError as exc:
        status = int(exc.code)
        raw = exc.read()
    except URLError as exc:
        raise RuntimeError(f"HTTP evidence request failed: {exc.reason}") from exc
    try:
        decoded = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"HTTP evidence response was not JSON (status {status})") from exc
    if not isinstance(decoded, Mapping):
        raise ValueError(f"HTTP evidence response must be a JSON object (status {status})")
    return status, decoded


def _bounded_runtime_identity(payload: Mapping[str, Any], model: str) -> dict[str, Any]:
    models = payload.get("models")
    selected = models.get(model) if isinstance(models, Mapping) else None
    if not isinstance(selected, Mapping):
        selected = {}
    model_info = selected.get("model") if isinstance(selected.get("model"), Mapping) else {}
    runtime = selected.get("runtime") if isinstance(selected.get("runtime"), Mapping) else {}
    return {
        "protocol_version": payload.get("protocol_version"),
        "model_key": model,
        "model_id": model_info.get("id"),
        "artifact_digest": model_info.get("artifact_digest"),
        "verification": model_info.get("verification"),
        "runtime_name": runtime.get("name"),
        "runtime_version": runtime.get("version"),
        "config_digest": runtime.get("config_digest"),
        "runtime_fingerprint": runtime.get("fingerprint"),
        "evidence_grade": runtime.get("evidence_grade"),
    }


def _chat_summary(status: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    message: Mapping[str, Any] = {}
    if isinstance(choices, Sequence) and not isinstance(choices, (str, bytes)) and choices:
        first = choices[0]
        if isinstance(first, Mapping) and isinstance(first.get("message"), Mapping):
            message = first["message"]
    content = message.get("content")
    if not isinstance(content, str):
        candidate = payload.get("content")
        content = candidate if isinstance(candidate, str) else ""
    lowered = content.lower()
    detail = payload.get("detail")
    error_code = None
    if isinstance(detail, Mapping):
        candidate = detail.get("code") or detail.get("type")
        if isinstance(candidate, str):
            error_code = candidate[:80]
    return {
        "http_status": status,
        "completed": status == 200,
        "normal_content_present": bool(content.strip()),
        "normal_content_contains_thinking_boundary": "<think>" in lowered or "</think>" in lowered,
        "thinking_metadata_present": bool(payload.get("thinking")),
        "raw_output_metadata_present": bool(payload.get("raw_output")),
        "typed_error_present": status != 200 and (detail is not None or payload.get("error") is not None),
        "error_code": error_code,
    }


def capture_thinking_campaign(
    *,
    base_url: str,
    model: str,
    output: Path,
    timeout: float = 300.0,
) -> Mapping[str, Any]:
    """Exercise explicit OFF and ON-hidden requests without retaining prompt or output."""
    root = base_url.rstrip("/")
    _, identity_payload = _request_json(f"{root}/v1/runtime/identity", timeout=timeout)
    common = {
        "model": model,
        "messages": [{"role": "user", "content": _THINKING_PROMPT}],
        "temperature": 0,
        "show_thinking": False,
        "stream": False,
    }
    off_request = dict(common, enable_thinking=False)
    on_request = dict(common, enable_thinking=True)
    off_status, off_response = _request_json(
        f"{root}/v1/chat/completions",
        method="POST",
        payload=off_request,
        timeout=timeout,
    )
    on_status, on_response = _request_json(
        f"{root}/v1/chat/completions",
        method="POST",
        payload=on_request,
        timeout=timeout,
    )
    off = _chat_summary(off_status, off_response)
    on_hidden = _chat_summary(on_status, on_response)
    complete = bool(
        off["completed"]
        and on_hidden["completed"]
        and off["normal_content_present"]
        and on_hidden["normal_content_present"]
        and not off["normal_content_contains_thinking_boundary"]
        and not on_hidden["normal_content_contains_thinking_boundary"]
    )
    report: dict[str, Any] = {
        "schema_version": 1,
        "procedure": "explicit_thinking_on_off_hidden_v1",
        "runtime_identity": _bounded_runtime_identity(identity_payload, model),
        "requests": {
            "off": {"enable_thinking": False, "show_thinking": False, "temperature": 0, "stream": False},
            "on_hidden": {"enable_thinking": True, "show_thinking": False, "temperature": 0, "stream": False},
        },
        "off": off,
        "on_hidden": on_hidden,
        "complete": complete,
        "privacy": {
            "prompt_recorded": False,
            "output_recorded": False,
            "raw_response_recorded": False,
            "local_path_recorded": False,
        },
    }
    _write_json(output, report)
    return report


def _validate_eval_report(payload: Mapping[str, Any], label: str, errors: list[str]) -> None:
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        errors.append(f"{label}: missing manifest")
        return
    expected = {
        "test_set_id": "general-purpose",
        "test_set_version": "1.0.0",
        "seed": 0,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"{label}: {key} must be {value!r}")
    sample_ids = manifest.get("sample_ids")
    if not isinstance(sample_ids, Sequence) or isinstance(sample_ids, (str, bytes)) or len(sample_ids) != 10:
        errors.append(f"{label}: sample_ids must contain exactly 10 entries")
    reasoning = manifest.get("reasoning_profile")
    if not isinstance(reasoning, Mapping):
        errors.append(f"{label}: reasoning_profile is required")
    else:
        if reasoning.get("requested") != "off" or reasoning.get("effective") != "off":
            errors.append(f"{label}: requested/effective reasoning must both be off")
    if payload.get("complete") is not True:
        errors.append(f"{label}: report must be complete")
    results = payload.get("results")
    if not isinstance(results, Sequence) or isinstance(results, (str, bytes)):
        errors.append(f"{label}: results are required")
        return
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            errors.append(f"{label}: result {index} must be an object")
            continue
        if result.get("succeeded") is not True and not isinstance(result.get("error_code"), str):
            errors.append(f"{label}: result {index} must succeed or carry explicit error_code")


def _resource_smoke_complete(payload: Mapping[str, Any], errors: list[str]) -> bool:
    success = payload.get("success")
    rejection = payload.get("rejection")
    if not isinstance(success, Mapping) or not isinstance(rejection, Mapping):
        errors.append("resource-policy-smoke: success/rejection objects are required")
        return False
    checks = [
        (success.get("admission") == "admit", "success admission must be admit"),
        (success.get("inference_http_status") == 200, "inference_http_status must be 200"),
        (isinstance(success.get("committed_bytes"), int) and success.get("committed_bytes", 0) > 0, "committed_bytes must be positive while resident"),
        (success.get("committed_bytes_after_unload") == 0, "committed bytes must return to zero"),
        (success.get("reserved_bytes_after_unload") == 0, "reserved bytes must return to zero"),
        (success.get("health_ok_after_unload") is True, "health must be green after unload"),
        (success.get("health_state_after_unload") == "cold", "health state must be cold after unload"),
        (rejection.get("admission") == "reject", "insufficient budget must reject"),
        (rejection.get("backend_load_reached") is False, "rejection must happen before backend load"),
        (payload.get("automatic_eviction_exercised") is False, "automatic eviction must remain false"),
    ]
    for ok, message in checks:
        if not ok:
            errors.append(f"resource-policy-smoke: {message}")
    return all(ok for ok, _ in checks)


def validate_hardware_bundle(directory: Path) -> Mapping[str, Any]:
    root = directory.expanduser()
    required = {
        "thinking": "thinking-campaign.json",
        "eval_a": "evaluation-off-a.json",
        "eval_b": "evaluation-off-b.json",
        "reclamation_a": "reclamation-a.json",
        "reclamation_b": "reclamation-b.json",
        "reclamation_review": "reclamation-review.json",
        "resource": "resource-policy-smoke.json",
    }
    errors: list[str] = []
    payloads: dict[str, Mapping[str, Any]] = {}
    for key, name in required.items():
        path = root / name
        if not path.is_file():
            errors.append(f"missing required evidence file: {name}")
            continue
        try:
            payloads[key] = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid {name}: {exc}")

    thinking_ok = False
    thinking = payloads.get("thinking")
    if thinking is not None:
        requests = thinking.get("requests")
        off_request = requests.get("off") if isinstance(requests, Mapping) else None
        on_request = requests.get("on_hidden") if isinstance(requests, Mapping) else None
        thinking_ok = bool(
            thinking.get("schema_version") == 1
            and thinking.get("complete") is True
            and isinstance(off_request, Mapping)
            and off_request.get("enable_thinking") is False
            and off_request.get("show_thinking") is False
            and isinstance(on_request, Mapping)
            and on_request.get("enable_thinking") is True
            and on_request.get("show_thinking") is False
        )
        if not thinking_ok:
            errors.append("thinking-campaign: explicit OFF/ON-hidden campaign is not complete")

    evaluation_ok = False
    eval_comparison: Mapping[str, Any] | None = None
    eval_a = payloads.get("eval_a")
    eval_b = payloads.get("eval_b")
    if eval_a is not None and eval_b is not None:
        _validate_eval_report(eval_a, "evaluation-off-a", errors)
        _validate_eval_report(eval_b, "evaluation-off-b", errors)
        try:
            summary_a = summarize_report_payload(eval_a)
            summary_b = summarize_report_payload(eval_b)
            comparison = compare_run_summaries(summary_a, summary_b)
            eval_comparison = comparison.to_public_dict()
            evaluation_ok = bool(
                comparison.comparable
                and comparison.evidence_grade
                and comparison.attribution_safe
                and summary_a.sample_count == 10
                and summary_b.sample_count == 10
            )
            if not evaluation_ok:
                errors.append("evaluation repeat: runs are not attribution-safe comparable evidence")
        except ValueError as exc:
            errors.append(f"evaluation repeat: {exc}")

    reclamation_ok = False
    reclamation_summary: Mapping[str, Any] | None = None
    reclamation_a = payloads.get("reclamation_a")
    reclamation_b = payloads.get("reclamation_b")
    stored_review = payloads.get("reclamation_review")
    if reclamation_a is not None and reclamation_b is not None:
        recomputed = review_hardware_evidence(
            [reclamation_a, reclamation_b],
            settings=EvidenceReviewSettings(
                min_reports=2,
                min_complete_cycles=6,
                require_verified_identity=True,
                require_zero_error_cycles=True,
            ),
        ).to_public_dict()
        reclamation_summary = recomputed
        reclamation_ok = bool(
            recomputed.get("report_count") == 2
            and recomputed.get("compatible_report_count") == 2
            and isinstance(recomputed.get("complete_windows"), int)
            and recomputed.get("complete_windows", 0) >= 6
            and recomputed.get("error_cycles") == 0
            and recomputed.get("automatic_eviction_recommendation") == "not_provided"
            and recomputed.get("production_safety_claim") is False
        )
        if not reclamation_ok:
            errors.append("reclamation: two compatible verified reports with six complete error-free windows are required")
        if stored_review is None:
            errors.append("reclamation-review.json is required")
        else:
            for key in (
                "state",
                "report_count",
                "compatible_report_count",
                "complete_windows",
                "error_cycles",
                "automatic_eviction_recommendation",
                "production_safety_claim",
            ):
                if stored_review.get(key) != recomputed.get(key):
                    errors.append(f"reclamation-review: stored {key} does not match conservative recomputation")

    resource_ok = False
    resource = payloads.get("resource")
    if resource is not None:
        resource_ok = _resource_smoke_complete(resource, errors)

    summary: dict[str, Any] = {
        "schema_version": 1,
        "procedure": "l2_representative_device_bundle_review_v1",
        "complete": bool(thinking_ok and evaluation_ok and reclamation_ok and resource_ok and not errors),
        "gates": {
            "thinking_on_off": thinking_ok,
            "evaluation_repeat": evaluation_ok,
            "reclamation": reclamation_ok,
            "resource_policy_smoke": resource_ok,
        },
        "evaluation_comparison": eval_comparison,
        "reclamation_review": reclamation_summary,
        "errors": errors,
        "privacy": {
            "input_paths_retained": False,
            "prompt_or_output_retained": False,
        },
    }
    return summary


def _contains_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return bool(
        "/users/" in lowered
        or "/home/" in lowered
        or "file://" in lowered
        or _WINDOWS_PATH.search(value)
        or _EMAIL.search(value)
        or "sk-" in lowered
    )


def _validate_sanitized_text(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be non-empty text")
        return
    if len(value) > 500:
        errors.append(f"{label} exceeds 500 characters")
    if _contains_sensitive_text(value):
        errors.append(f"{label} appears to contain private path, email or secret-like data")


def validate_product_ui_evidence(
    *,
    accessibility: Mapping[str, Any] | None,
    usability: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    required_accessibility = {
        "keyboard-primary-shell",
        "focus-order-and-visibility",
        "accessibility-tree-or-screen-reader",
        "zoom-and-text-scaling",
        "reduced-motion",
        "error-loading-empty-disabled-states",
    }
    required_journeys = {
        "control-plane-status-and-navigation",
        "chat-inference-and-recovery",
        "advanced-control-discovery",
        "evidence-interpretation",
    }
    errors: list[str] = []
    accessibility_present = False
    accessibility_ready = False
    accessibility_blocking = 0
    if accessibility is not None:
        if accessibility.get("schema_version") != 1 or accessibility.get("evidence_kind") != "manual_accessibility":
            errors.append("manual accessibility evidence has invalid schema/evidence_kind")
        revision = accessibility.get("source_revision")
        if not isinstance(revision, str) or not _HEX40.fullmatch(revision):
            errors.append("manual accessibility source_revision must be a 40-char lowercase commit SHA")
        study_id = accessibility.get("study_id")
        if not isinstance(study_id, str) or not study_id.strip() or study_id.startswith("example-"):
            errors.append("manual accessibility study_id must identify a real non-example review")
        checks = accessibility.get("checks")
        seen: set[str] = set()
        blocking = 0
        if not isinstance(checks, Sequence) or isinstance(checks, (str, bytes)):
            errors.append("manual accessibility checks must be an array")
            checks = []
        for index, item in enumerate(checks):
            if not isinstance(item, Mapping):
                errors.append(f"manual accessibility check {index} must be an object")
                continue
            check_id = item.get("check_id")
            if not isinstance(check_id, str) or check_id not in required_accessibility:
                errors.append(f"manual accessibility check {index} has unknown check_id")
                continue
            if check_id in seen:
                errors.append(f"manual accessibility duplicate check_id: {check_id}")
            seen.add(check_id)
            outcome = item.get("outcome")
            if outcome not in {"pass", "fail", "inconclusive", "not-applicable"}:
                errors.append(f"manual accessibility {check_id} has invalid outcome")
            if outcome in {"fail", "inconclusive"}:
                blocking += 1
            severity = item.get("severity")
            if severity not in {"none", "low", "medium", "high", "critical"}:
                errors.append(f"manual accessibility {check_id} has invalid severity")
            _validate_sanitized_text(item.get("sanitized_observation"), f"manual accessibility {check_id} observation", errors)
        missing = sorted(required_accessibility - seen)
        if missing:
            errors.append("manual accessibility missing checks: " + ", ".join(missing))
        accessibility_present = not missing and bool(checks)
        accessibility_blocking = blocking
        accessibility_ready = accessibility_present and blocking == 0 and not any(
            error.startswith("manual accessibility") for error in errors
        )

    usability_present = False
    usability_ready = False
    usability_blocking = 0
    if usability is not None:
        if usability.get("schema_version") != 1 or usability.get("evidence_kind") != "representative_user_usability":
            errors.append("usability evidence has invalid schema/evidence_kind")
        revision = usability.get("source_revision")
        if not isinstance(revision, str) or not _HEX40.fullmatch(revision):
            errors.append("usability source_revision must be a 40-char lowercase commit SHA")
        records = usability.get("records")
        seen_journeys: set[str] = set()
        blocking = 0
        allowed_fields = {
            "study_id",
            "journey_id",
            "task_completed",
            "needed_recovery",
            "assistance_required",
            "duration_bucket",
            "severity",
            "sanitized_observation",
        }
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            errors.append("usability records must be an array")
            records = []
        for index, record in enumerate(records):
            if not isinstance(record, Mapping):
                errors.append(f"usability record {index} must be an object")
                continue
            extra = sorted(set(record) - allowed_fields)
            if extra:
                errors.append(f"usability record {index} contains non-allow-listed fields: {', '.join(extra)}")
            study_id = record.get("study_id")
            if not isinstance(study_id, str) or not study_id.strip() or study_id.startswith("example-"):
                errors.append(f"usability record {index} must identify a real non-example study")
            journey = record.get("journey_id")
            if not isinstance(journey, str) or journey not in required_journeys:
                errors.append(f"usability record {index} has unknown journey_id")
            else:
                seen_journeys.add(journey)
            for key in ("task_completed", "needed_recovery", "assistance_required"):
                if not isinstance(record.get(key), bool):
                    errors.append(f"usability record {index}.{key} must be boolean")
            if record.get("duration_bucket") not in {"under-30s", "30s-2m", "over-2m", "not-measured"}:
                errors.append(f"usability record {index} has invalid duration_bucket")
            severity = record.get("severity")
            if severity not in {"none", "low", "medium", "high", "critical"}:
                errors.append(f"usability record {index} has invalid severity")
            if severity in {"high", "critical"}:
                blocking += 1
            _validate_sanitized_text(record.get("sanitized_observation"), f"usability record {index} observation", errors)
        missing = sorted(required_journeys - seen_journeys)
        if missing:
            errors.append("usability evidence missing journeys: " + ", ".join(missing))
        usability_present = not missing and bool(records)
        usability_blocking = blocking
        usability_ready = usability_present and blocking == 0 and not any(
            error.startswith("usability") for error in errors
        )

    return {
        "schema_version": 1,
        "procedure": "product_ui_human_evidence_review_v1",
        "manual_accessibility": {
            "evidence_present": accessibility_present,
            "acceptance_ready": accessibility_ready,
            "blocking_findings": accessibility_blocking,
        },
        "representative_user_usability": {
            "evidence_present": usability_present,
            "acceptance_ready": usability_ready,
            "blocking_findings": usability_blocking,
        },
        "full_product_ui_evidence_ready": bool(accessibility_ready and usability_ready and not errors),
        "errors": errors,
        "baseline_mutated": False,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture/validate real L2 evidence without promoting claims automatically.")
    sub = parser.add_subparsers(dest="command", required=True)

    thinking = sub.add_parser("capture-thinking", help="Run explicit OFF/ON-hidden requests and retain only bounded evidence.")
    thinking.add_argument("--base-url", default="http://127.0.0.1:8000")
    thinking.add_argument("--model", required=True)
    thinking.add_argument("--output", required=True)
    thinking.add_argument("--timeout", type=float, default=300.0)

    hardware = sub.add_parser("validate-hardware-bundle", help="Validate the complete representative-device evidence directory.")
    hardware.add_argument("--directory", required=True)
    hardware.add_argument("--output", default=None)

    product = sub.add_parser("validate-product-ui", help="Validate bounded manual accessibility/usability evidence.")
    product.add_argument("--accessibility", default=None)
    product.add_argument("--usability", default=None)
    product.add_argument("--output", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "capture-thinking":
            report = capture_thinking_campaign(
                base_url=args.base_url,
                model=args.model,
                output=Path(args.output),
                timeout=args.timeout,
            )
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0 if report.get("complete") is True else 2
        if args.command == "validate-hardware-bundle":
            summary = validate_hardware_bundle(Path(args.directory))
        else:
            accessibility = _load_json(Path(args.accessibility)) if args.accessibility else None
            usability = _load_json(Path(args.usability)) if args.usability else None
            summary = validate_product_ui_evidence(accessibility=accessibility, usability=usability)
        if args.output:
            _write_json(Path(args.output), summary)
        print(json.dumps(summary, indent=2, sort_keys=True))
        complete_key = "complete" if args.command == "validate-hardware-bundle" else "full_product_ui_evidence_ready"
        return 0 if summary.get(complete_key) is True else 2
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Evidence bridge failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
