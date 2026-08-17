"""Evaluation history summaries and compatibility-aware run comparisons.

This module deliberately reports deltas rather than automated "better/worse"
verdicts. Dataset/sample identity is required for comparison. Runtime
fingerprints and explicit reasoning profiles make a comparison evidence-grade;
changed or legacy-unknown request identity is surfaced as a confounder rather
than silently attributed to the evaluated model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class EvaluationRunSummary:
    run_id: str
    model: str
    test_set_identity: str
    sample_ids: tuple[str, ...]
    runtime_fingerprint: str | None
    reasoning_profile: Mapping[str, Any] | None
    complete: bool
    sample_count: int
    succeeded_count: int
    scored_count: int
    objective_quality_mean: float | None
    execution_success_rate: float | None
    mean_wall_time_seconds: float | None
    total_input_tokens: int | None
    total_output_tokens: int | None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "model": self.model,
            "test_set_identity": self.test_set_identity,
            "sample_ids": list(self.sample_ids),
            "runtime_fingerprint": self.runtime_fingerprint,
            "reasoning_profile": (
                dict(self.reasoning_profile)
                if self.reasoning_profile is not None
                else None
            ),
            "complete": self.complete,
            "sample_count": self.sample_count,
            "succeeded_count": self.succeeded_count,
            "scored_count": self.scored_count,
            "objective_quality_mean": self.objective_quality_mean,
            "execution_success_rate": self.execution_success_rate,
            "mean_wall_time_seconds": self.mean_wall_time_seconds,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }


@dataclass(frozen=True, slots=True)
class EvaluationComparison:
    baseline_run_id: str
    candidate_run_id: str
    comparable: bool
    evidence_grade: bool
    attribution_safe: bool
    reasons: tuple[str, ...]
    deltas: Mapping[str, float | int | None]

    def to_public_dict(self) -> dict[str, object]:
        return {
            "baseline_run_id": self.baseline_run_id,
            "candidate_run_id": self.candidate_run_id,
            "comparable": self.comparable,
            "evidence_grade": self.evidence_grade,
            "attribution_safe": self.attribution_safe,
            "reasons": list(self.reasons),
            "deltas": dict(self.deltas),
        }


def summarize_report_payload(payload: Mapping[str, Any]) -> EvaluationRunSummary:
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("evaluation report is missing manifest")
    raw_results = payload.get("results")
    if not isinstance(raw_results, Sequence) or isinstance(raw_results, (str, bytes)):
        raise ValueError("evaluation report is missing results")

    results = [item for item in raw_results if isinstance(item, Mapping)]
    sample_ids = tuple(str(value) for value in manifest.get("sample_ids", ()))
    scores: list[float] = []
    wall_times: list[float] = []
    succeeded = 0
    input_tokens: list[int] = []
    output_tokens: list[int] = []

    for result in results:
        if result.get("succeeded") is True:
            succeeded += 1
        raw_scores = result.get("scores")
        if isinstance(raw_scores, Sequence) and not isinstance(raw_scores, (str, bytes)):
            for score in raw_scores:
                if not isinstance(score, Mapping):
                    continue
                value = _number(score.get("value"))
                if value is not None:
                    scores.append(float(value))
        metrics = result.get("metrics")
        if not isinstance(metrics, Mapping):
            continue
        wall = _number(metrics.get("wall_time_seconds"))
        if wall is not None and wall >= 0:
            wall_times.append(float(wall))
        in_tokens = _first_nonnegative_int(metrics, "input_tokens", "prompt_tokens")
        out_tokens = _first_nonnegative_int(metrics, "output_tokens", "completion_tokens")
        if in_tokens is not None:
            input_tokens.append(in_tokens)
        if out_tokens is not None:
            output_tokens.append(out_tokens)

    count = len(results)
    fingerprint = manifest.get("runtime_fingerprint")
    raw_reasoning = manifest.get("reasoning_profile")
    reasoning_profile = dict(raw_reasoning) if isinstance(raw_reasoning, Mapping) else None
    return EvaluationRunSummary(
        run_id=str(manifest.get("run_id") or ""),
        model=str(manifest.get("model") or ""),
        test_set_identity=str(manifest.get("test_set_identity") or ""),
        sample_ids=sample_ids,
        runtime_fingerprint=str(fingerprint) if fingerprint is not None else None,
        reasoning_profile=reasoning_profile,
        complete=bool(payload.get("complete")),
        sample_count=count,
        succeeded_count=succeeded,
        scored_count=len(scores),
        objective_quality_mean=(sum(scores) / len(scores)) if scores else None,
        execution_success_rate=(succeeded / count) if count else None,
        mean_wall_time_seconds=(sum(wall_times) / len(wall_times)) if wall_times else None,
        total_input_tokens=sum(input_tokens) if input_tokens else None,
        total_output_tokens=sum(output_tokens) if output_tokens else None,
    )


def compare_run_summaries(
    baseline: EvaluationRunSummary,
    candidate: EvaluationRunSummary,
) -> EvaluationComparison:
    reasons: list[str] = []
    comparable = True
    if not baseline.complete or not candidate.complete:
        comparable = False
        reasons.append("both runs must be complete")
    if baseline.test_set_identity != candidate.test_set_identity:
        comparable = False
        reasons.append("test-set identity differs")
    if baseline.sample_ids != candidate.sample_ids:
        comparable = False
        reasons.append("selected sample IDs differ")

    reasoning_known = (
        baseline.reasoning_profile is not None
        and candidate.reasoning_profile is not None
    )
    if comparable and not reasoning_known:
        reasons.append("reasoning profile missing from one or both runs")

    evidence_grade = (
        comparable
        and reasoning_known
        and baseline.runtime_fingerprint is not None
        and candidate.runtime_fingerprint is not None
    )
    if comparable and baseline.runtime_fingerprint is None or (
        comparable and candidate.runtime_fingerprint is None
    ):
        reasons.append("runtime fingerprint missing from one or both runs")

    fingerprint_matches = (
        evidence_grade
        and baseline.runtime_fingerprint == candidate.runtime_fingerprint
    )
    reasoning_matches = (
        reasoning_known
        and dict(baseline.reasoning_profile or {}) == dict(candidate.reasoning_profile or {})
    )
    model_matches = baseline.model == candidate.model
    attribution_safe = bool(
        comparable
        and evidence_grade
        and fingerprint_matches
        and reasoning_matches
        and model_matches
    )
    if comparable and evidence_grade and not fingerprint_matches:
        reasons.append("runtime fingerprint changed; deltas are descriptive only")
    if comparable and reasoning_known and not reasoning_matches:
        reasons.append("reasoning profile changed; deltas are descriptive only")
    if comparable and not model_matches:
        reasons.append("model changed; deltas describe a cross-model comparison")

    deltas = {
        "objective_quality_mean": _delta(
            baseline.objective_quality_mean,
            candidate.objective_quality_mean,
        ),
        "execution_success_rate": _delta(
            baseline.execution_success_rate,
            candidate.execution_success_rate,
        ),
        "mean_wall_time_seconds": _delta(
            baseline.mean_wall_time_seconds,
            candidate.mean_wall_time_seconds,
        ),
        "total_input_tokens": _delta(
            baseline.total_input_tokens,
            candidate.total_input_tokens,
        ),
        "total_output_tokens": _delta(
            baseline.total_output_tokens,
            candidate.total_output_tokens,
        ),
    }
    if not comparable:
        deltas = {key: None for key in deltas}

    return EvaluationComparison(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        comparable=comparable,
        evidence_grade=evidence_grade,
        attribution_safe=attribution_safe,
        reasons=tuple(reasons),
        deltas=deltas,
    )


def _delta(
    baseline: float | int | None,
    candidate: float | int | None,
) -> float | int | None:
    if baseline is None or candidate is None:
        return None
    return candidate - baseline


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _first_nonnegative_int(metrics: Mapping[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = metrics.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    return None
