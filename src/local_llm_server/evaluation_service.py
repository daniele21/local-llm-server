"""Resident-runtime evaluation service and local report persistence."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from .backend_request import build_backend_request
from .core.contracts import (
    ErrorCode,
    InferenceError,
    InferenceRequest,
    InferenceResult,
    TaskType,
    TerminationReason,
)
from .evaluation import (
    EvaluationReport,
    EvaluationSampleResult,
    SampleSelection,
    Score,
    TestSet,
    build_run_manifest,
)
from .evaluation_builtin import DeterministicObjectiveScorer, GENERAL_PURPOSE_V1
from .evaluation_reasoning import (
    EvaluationReasoningPolicy,
    default_reasoning_policy,
    resolve_evaluation_reasoning_profile,
)
from .evaluation_runner import EvaluationRunner
from .evaluation_testsets import CustomTestSetStore
from .runtime_evidence import attached_runtime_identity


_BUILTIN_TEST_SETS: dict[tuple[str, str], TestSet] = {
    (GENERAL_PURPOSE_V1.test_set_id, GENERAL_PURPOSE_V1.version): GENERAL_PURPOSE_V1,
}


@dataclass(frozen=True, slots=True)
class EvaluationRunRequest:
    model: str
    test_set_id: str = "general-purpose"
    test_set_version: str | None = None
    sample_count: int = 20
    seed: int = 0
    reasoning_policy: EvaluationReasoningPolicy | str | None = None
    retain_content: bool = True

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("model must be non-empty")
        if self.test_set_version is not None and not self.test_set_version.strip():
            raise ValueError("test_set_version must be non-empty when provided")
        if self.sample_count < 10 or self.sample_count % 10 != 0:
            raise ValueError("sample_count must be a positive multiple of 10")
        if self.reasoning_policy is not None:
            EvaluationReasoningPolicy(str(self.reasoning_policy))


@dataclass(frozen=True, slots=True)
class EvaluationRunOutcome:
    report: EvaluationReport
    evidence_grade: bool
    persisted_path: str | None = None


class ResidentRuntimeExecutor:
    """Execute canonical deterministic evaluation requests on one resident runtime."""

    def __init__(self, manager: Any, *, runtime: Any | None = None) -> None:
        self.manager = manager
        self.runtime = runtime

    def execute(self, request: InferenceRequest) -> InferenceResult:
        if request.task not in {TaskType.CHAT, TaskType.STRUCTURED_GENERATION}:
            raise InferenceError(
                ErrorCode.UNSUPPORTED_TASK,
                f"evaluation executor does not support task {request.task.value}",
            )

        runtime = self._resolve_runtime(request)
        canonical = _request_with_messages(request)
        prepared = build_backend_request(
            canonical,
            runtime_config=runtime.cfg,
            runtime_model_id=runtime.model_id,
        )
        kwargs = dict(prepared.kwargs)

        started = time.perf_counter()
        with self.manager.lease_runtime(runtime):
            runtime.mark_started(int(prepared.max_tokens or 0))
            try:
                raw = runtime.engine.complete(kwargs)
            except InferenceError:
                raise
            except Exception as exc:
                raise InferenceError(
                    ErrorCode.BACKEND_ERROR,
                    "evaluation backend execution failed",
                    retryable=False,
                    details={"backend": getattr(runtime.engine, "backend", "unknown")},
                ) from exc
            finally:
                runtime.mark_idle()
        elapsed = time.perf_counter() - started

        content = _extract_content(raw)
        usage = _numeric_usage(raw.get("usage"))
        usage["wall_time_seconds"] = elapsed
        return InferenceResult(
            task=request.task,
            model=runtime.model_id,
            content=content,
            termination_reason=_termination_reason(raw),
            usage=usage,
            metadata={"backend": getattr(runtime.engine, "backend", runtime.cfg.get("backend", "unknown"))},
        )

    def _resolve_runtime(self, request: InferenceRequest) -> Any:
        if self.runtime is not None:
            selected = self.runtime
            if request.model not in {None, selected.key, selected.model_id}:
                raise InferenceError(
                    ErrorCode.MODEL_NOT_RESIDENT,
                    "evaluation request does not match the pinned resident runtime",
                    retryable=False,
                    details={"model": request.model},
                )
            return selected

        try:
            return self.manager.resolve(request.model)
        except LookupError as exc:
            raise InferenceError(
                ErrorCode.MODEL_NOT_RESIDENT,
                "selected evaluation model is not resident",
                retryable=True,
                details={"model": request.model},
            ) from exc


class EvaluationStore:
    """Simple immutable local JSON report store."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser()

    def save(self, report: EvaluationReport) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{report.manifest.run_id}.json"
        if target.exists():
            raise FileExistsError(f"evaluation run already exists: {report.manifest.run_id}")
        temp = target.with_suffix(".json.tmp")
        temp.write_text(
            json.dumps(
                report_to_dict(
                    report,
                    include_content=True,
                    include_output=report.manifest.content_retained,
                ),
                sort_keys=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        os.replace(temp, target)
        return target

    def list_run_ids(self) -> tuple[str, ...]:
        if not self.root.exists():
            return ()
        return tuple(sorted(path.stem for path in self.root.glob("*.json") if path.is_file()))


class EvaluationService:
    def __init__(
        self,
        manager: Any,
        *,
        store: EvaluationStore | None = None,
        test_set_store: CustomTestSetStore | None = None,
    ) -> None:
        self.manager = manager
        self.store = store
        self.test_set_store = test_set_store

    def list_test_sets(self) -> tuple[dict[str, object], ...]:
        entries: list[tuple[TestSet, str]] = [
            (test_set, "built-in") for test_set in _BUILTIN_TEST_SETS.values()
        ]
        if self.test_set_store is not None:
            entries.extend(
                (test_set, "custom")
                for test_set in self.test_set_store.list_test_sets()
            )
        return tuple(
            {
                "id": test_set.test_set_id,
                "version": test_set.version,
                "identity": test_set.identity,
                "sample_count": len(test_set.samples),
                "provenance": dict(test_set.provenance),
                "source": source,
                "default_reasoning_policy": default_reasoning_policy(test_set.test_set_id).value,
            }
            for test_set, source in sorted(
                entries,
                key=lambda item: (item[0].test_set_id, item[0].version, item[1]),
            )
        )

    def run(self, request: EvaluationRunRequest) -> EvaluationRunOutcome:
        test_set = self._resolve_test_set(request.test_set_id, request.test_set_version)
        if request.sample_count > len(test_set.samples):
            raise ValueError(
                f"sample_count {request.sample_count} exceeds dataset size {len(test_set.samples)}"
            )

        try:
            runtime = self.manager.resolve(request.model)
        except LookupError as exc:
            raise InferenceError(
                ErrorCode.MODEL_NOT_RESIDENT,
                "selected evaluation model is not resident",
                retryable=True,
                details={"model": request.model},
            ) from exc

        requested_policy = (
            EvaluationReasoningPolicy(str(request.reasoning_policy))
            if request.reasoning_policy is not None
            else default_reasoning_policy(test_set.test_set_id)
        )
        reasoning_profile = resolve_evaluation_reasoning_profile(
            requested_policy,
            runtime.cfg,
        )

        identity = attached_runtime_identity(runtime)
        fingerprint = identity.fingerprint if identity is not None else None
        selection = SampleSelection(limit=request.sample_count, seed=request.seed)
        manifest = build_run_manifest(
            run_id=uuid.uuid4().hex,
            test_set=test_set,
            selection=selection,
            model=runtime.key,
            runtime_fingerprint=fingerprint,
            reasoning_profile=reasoning_profile,
            content_retained=request.retain_content,
        )
        report = EvaluationRunner(
            ResidentRuntimeExecutor(self.manager, runtime=runtime),
            (DeterministicObjectiveScorer(),),
        ).run(manifest=manifest, test_set=test_set)

        path = self.store.save(report) if self.store is not None else None
        return EvaluationRunOutcome(
            report=report,
            evidence_grade=fingerprint is not None,
            persisted_path=str(path) if path is not None else None,
        )

    def _resolve_test_set(self, test_set_id: str, version: str | None) -> TestSet:
        built_matches = [
            test_set
            for (current_id, current_version), test_set in _BUILTIN_TEST_SETS.items()
            if current_id == test_set_id and (version is None or current_version == version)
        ]
        if version is None and len(built_matches) == 1:
            return built_matches[0]
        if version is not None and built_matches:
            return built_matches[0]

        if self.test_set_store is not None:
            custom = self.test_set_store.resolve(test_set_id, version)
            if custom is not None:
                return custom

        suffix = f"@{version}" if version else ""
        raise ValueError(f"unknown test set: {test_set_id}{suffix}")


def report_to_dict(
    report: EvaluationReport,
    *,
    include_content: bool = False,
    include_output: bool = False,
) -> dict[str, object]:
    manifest = report.manifest
    return {
        "manifest": {
            "run_id": manifest.run_id,
            "test_set_id": manifest.test_set_id,
            "test_set_version": manifest.test_set_version,
            "test_set_identity": manifest.test_set_identity,
            "sample_ids": list(manifest.sample_ids),
            "model": manifest.model,
            "task_types": [task.value for task in manifest.task_types],
            "seed": manifest.seed,
            "runtime_fingerprint": manifest.runtime_fingerprint,
            "reasoning_profile": (
                manifest.reasoning_profile.to_dict()
                if manifest.reasoning_profile is not None
                else None
            ),
            "content_retained": manifest.content_retained,
        },
        "complete": report.complete,
        "results": [
            _sample_result_to_dict(
                result,
                include_content=include_content,
                include_output=include_output,
            )
            for result in report.results
        ],
    }


def _sample_result_to_dict(
    result: EvaluationSampleResult,
    *,
    include_content: bool = False,
    include_output: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "sample_id": result.sample_id,
        "succeeded": result.succeeded,
        "scores": [_score_to_dict(score) for score in result.scores],
        "error_code": result.error_code,
        "metrics": dict(result.metrics),
    }
    if include_content:
        content: dict[str, object] = {
            "input": result.input_text,
            "expected": dict(result.expected),
        }
        if include_output:
            content["output"] = result.output_text
        payload["content"] = content
    return payload


def _score_to_dict(score: Score) -> dict[str, object]:
    return {
        "name": score.name,
        "value": score.value,
        "passed": score.passed,
        "details": dict(score.details),
    }


def _request_with_messages(request: InferenceRequest) -> InferenceRequest:
    if request.messages:
        return request
    if request.input_text is None:
        raise InferenceError(ErrorCode.INVALID_REQUEST, "evaluation request has no input")
    return replace(
        request,
        messages=({"role": "user", "content": request.input_text},),
    )


def _extract_content(raw: Mapping[str, Any]) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], Mapping):
        return ""
    choice = choices[0]
    message = choice.get("message")
    if isinstance(message, Mapping) and isinstance(message.get("content"), str):
        return str(message["content"])
    text = choice.get("text")
    return str(text) if isinstance(text, str) else ""


def _termination_reason(raw: Mapping[str, Any]) -> TerminationReason:
    choices = raw.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], Mapping):
        finish = choices[0].get("finish_reason")
        if finish == "length":
            return TerminationReason.MAX_TOKENS
    return TerminationReason.STOP


def _numeric_usage(value: Any) -> dict[str, int | float]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    }
