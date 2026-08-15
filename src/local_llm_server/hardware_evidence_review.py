"""Conservative review of repeated reclamation hardware reports.

The reviewer answers whether a set of reports is compatible and sufficiently
repeated to describe an observation pattern. It deliberately does not recommend
automatic eviction or convert observations into a production-safety verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class EvidenceReviewState(str, Enum):
    INSUFFICIENT = "insufficient"
    INCOMPATIBLE = "incompatible"
    MIXED = "mixed"
    CONSISTENT_RECOVERY_OBSERVED = "consistent_recovery_observed"
    CONSISTENT_NO_RECOVERY_OBSERVED = "consistent_no_recovery_observed"


@dataclass(frozen=True, slots=True)
class EvidenceReviewSettings:
    min_reports: int = 2
    min_complete_cycles: int = 6
    require_verified_identity: bool = True
    require_zero_error_cycles: bool = True

    def __post_init__(self) -> None:
        if self.min_reports < 1:
            raise ValueError("min_reports must be >= 1")
        if self.min_complete_cycles < 1:
            raise ValueError("min_complete_cycles must be >= 1")


@dataclass(frozen=True, slots=True)
class HardwareEvidenceReview:
    state: EvidenceReviewState
    report_count: int
    compatible_report_count: int
    total_cycles: int
    complete_windows: int
    error_cycles: int
    recovery_observed: int
    no_recovery_observed: int
    inconclusive: int
    identity_grade: str | None
    reasons: tuple[str, ...]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "report_count": self.report_count,
            "compatible_report_count": self.compatible_report_count,
            "total_cycles": self.total_cycles,
            "complete_windows": self.complete_windows,
            "error_cycles": self.error_cycles,
            "observations": {
                "recovery_observed": self.recovery_observed,
                "no_recovery_observed": self.no_recovery_observed,
                "inconclusive": self.inconclusive,
            },
            "identity_grade": self.identity_grade,
            "reasons": list(self.reasons),
            "automatic_eviction_recommendation": "not_provided",
            "production_safety_claim": False,
            "interpretation": (
                "This review summarizes compatibility, repetition and observation "
                "consistency only. It does not authorize automatic eviction or "
                "establish memory-reclamation safety."
            ),
        }


def review_hardware_evidence(
    reports: Sequence[Mapping[str, Any]],
    *,
    settings: EvidenceReviewSettings | None = None,
) -> HardwareEvidenceReview:
    """Review reports that should represent the same runtime/hardware procedure."""
    cfg = settings or EvidenceReviewSettings()
    parsed = [_parse_report(report) for report in reports]
    valid = [item for item in parsed if item is not None]
    reasons: list[str] = []

    if len(valid) != len(reports):
        reasons.append("one_or_more_reports_have_invalid_schema")
    if not valid:
        return _result(
            state=EvidenceReviewState.INSUFFICIENT,
            report_count=len(reports),
            compatible_report_count=0,
            reasons=tuple(reasons or ["no_valid_reports"]),
        )

    reference_key = valid[0]["compatibility_key"]
    compatible = [item for item in valid if item["compatibility_key"] == reference_key]
    if len(compatible) != len(valid):
        reasons.append("runtime_hardware_or_procedure_identity_differs")
        return _aggregate_result(
            EvidenceReviewState.INCOMPATIBLE,
            reports=len(reports),
            compatible=compatible,
            reasons=tuple(reasons),
        )

    identity_grade = str(compatible[0]["identity_grade"] or "") or None
    if cfg.require_verified_identity and identity_grade != "verified":
        reasons.append("verified_identity_required")
    if len(compatible) < cfg.min_reports:
        reasons.append("insufficient_repeated_reports")

    totals = _aggregate(compatible)
    if totals["complete_windows"] < cfg.min_complete_cycles:
        reasons.append("insufficient_complete_cycles")
    if cfg.require_zero_error_cycles and totals["error_cycles"] > 0:
        reasons.append("lifecycle_errors_present")
    if totals["inconclusive"] > 0:
        reasons.append("inconclusive_cycles_present")

    if reasons:
        return _aggregate_result(
            EvidenceReviewState.INSUFFICIENT,
            reports=len(reports),
            compatible=compatible,
            reasons=tuple(reasons),
        )

    recovery = totals["recovery_observed"]
    no_recovery = totals["no_recovery_observed"]
    if recovery > 0 and no_recovery > 0:
        state = EvidenceReviewState.MIXED
        reasons.append("recovery_observations_are_not_consistent")
    elif recovery > 0:
        state = EvidenceReviewState.CONSISTENT_RECOVERY_OBSERVED
        reasons.append("all_conclusive_cycles_observed_recovery")
    elif no_recovery > 0:
        state = EvidenceReviewState.CONSISTENT_NO_RECOVERY_OBSERVED
        reasons.append("all_conclusive_cycles_observed_no_recovery")
    else:
        state = EvidenceReviewState.INSUFFICIENT
        reasons.append("no_conclusive_recovery_observations")

    return _aggregate_result(
        state,
        reports=len(reports),
        compatible=compatible,
        reasons=tuple(reasons),
    )


def _parse_report(report: Mapping[str, Any]) -> dict[str, Any] | None:
    if report.get("schema_version") != 1:
        return None
    outer_procedure = report.get("procedure")
    worker_report = report.get("report")
    if not isinstance(outer_procedure, Mapping) or not isinstance(worker_report, Mapping):
        return None
    descriptor = worker_report.get("descriptor")
    experiment = worker_report.get("experiment")
    if not isinstance(descriptor, Mapping) or not isinstance(experiment, Mapping):
        return None
    observations = experiment.get("observations")
    if not isinstance(observations, Mapping):
        return None

    numeric_fields = {
        "cycle_count": experiment.get("cycle_count"),
        "complete_windows": experiment.get("complete_windows"),
        "error_cycles": experiment.get("error_cycles"),
        "recovery_observed": observations.get("recovery_observed"),
        "no_recovery_observed": observations.get("no_recovery_observed"),
        "inconclusive": observations.get("inconclusive"),
    }
    if any(not _nonnegative_int(value) for value in numeric_fields.values()):
        return None

    compatibility_key = (
        descriptor.get("procedure"),
        descriptor.get("execution_isolation"),
        descriptor.get("model_id"),
        descriptor.get("backend"),
        descriptor.get("backend_version"),
        descriptor.get("artifact_sha256"),
        descriptor.get("config_digest"),
        _freeze(descriptor.get("hardware")),
        outer_procedure.get("name"),
        outer_procedure.get("max_tokens"),
        outer_procedure.get("settle_after_stop_seconds"),
    )
    return {
        "compatibility_key": compatibility_key,
        "identity_grade": descriptor.get("identity_grade"),
        **{key: int(value) for key, value in numeric_fields.items()},
    }


def _aggregate(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    fields = (
        "cycle_count",
        "complete_windows",
        "error_cycles",
        "recovery_observed",
        "no_recovery_observed",
        "inconclusive",
    )
    return {field: sum(int(item[field]) for item in items) for field in fields}


def _aggregate_result(
    state: EvidenceReviewState,
    *,
    reports: int,
    compatible: Sequence[Mapping[str, Any]],
    reasons: tuple[str, ...],
) -> HardwareEvidenceReview:
    totals = _aggregate(compatible)
    identity_grade = (
        str(compatible[0].get("identity_grade"))
        if compatible and compatible[0].get("identity_grade") is not None
        else None
    )
    return HardwareEvidenceReview(
        state=state,
        report_count=reports,
        compatible_report_count=len(compatible),
        total_cycles=totals["cycle_count"],
        complete_windows=totals["complete_windows"],
        error_cycles=totals["error_cycles"],
        recovery_observed=totals["recovery_observed"],
        no_recovery_observed=totals["no_recovery_observed"],
        inconclusive=totals["inconclusive"],
        identity_grade=identity_grade,
        reasons=reasons,
    )


def _result(
    *,
    state: EvidenceReviewState,
    report_count: int,
    compatible_report_count: int,
    reasons: tuple[str, ...],
) -> HardwareEvidenceReview:
    return HardwareEvidenceReview(
        state=state,
        report_count=report_count,
        compatible_report_count=compatible_report_count,
        total_cycles=0,
        complete_windows=0,
        error_cycles=0,
        recovery_observed=0,
        no_recovery_observed=0,
        inconclusive=0,
        identity_grade=None,
        reasons=reasons,
    )


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value
