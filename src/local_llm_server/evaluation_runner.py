"""Execution engine for reproducible local evaluation runs.

The runner is deliberately backend-neutral. Callers supply an executor that
accepts canonical ``InferenceRequest`` values and returns ``InferenceResult``.
This keeps D4 execution reusable across in-process engines, worker transports
and future remote comparison adapters without embedding backend logic here.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol, Sequence

from .core.contracts import (
    GenerationOptions,
    InferenceError,
    InferenceRequest,
    InferenceResult,
    OutputConstraints,
    TaskType,
)
from .evaluation import (
    EvaluationReport,
    EvaluationRunManifest,
    EvaluationSample,
    EvaluationSampleResult,
    Score,
    Scorer,
    TestSet,
)


class EvaluationExecutor(Protocol):
    """Backend-neutral execution boundary used by ``EvaluationRunner``."""

    def execute(self, request: InferenceRequest) -> InferenceResult: ...


def request_for_sample(
    sample: EvaluationSample,
    *,
    model: str,
    enable_thinking: bool | None = None,
) -> InferenceRequest:
    """Translate one evaluation sample into the canonical execution contract."""
    input_text = sample.payload.get("input")
    if input_text is not None and not isinstance(input_text, str):
        raise ValueError(f"sample {sample.sample_id!r} payload.input must be a string")

    output = OutputConstraints()
    if sample.task is TaskType.STRUCTURED_GENERATION:
        output = OutputConstraints(format="json_object")

    return InferenceRequest(
        task=sample.task,
        model=model,
        input_text=input_text,
        generation=GenerationOptions(
            temperature=0.0,
            enable_thinking=enable_thinking,
        ),
        output=output,
        stream=False,
        metadata={"evaluation_sample_id": sample.sample_id},
    )


@dataclass(slots=True)
class EvaluationRunner:
    executor: EvaluationExecutor
    scorers: Sequence[Scorer]

    def run(self, *, manifest: EvaluationRunManifest, test_set: TestSet) -> EvaluationReport:
        # Dataset identity is the outer reproducibility boundary. Reject a
        # manifest for a different dataset/version before interpreting its
        # sample IDs against the supplied set.
        if manifest.test_set_identity != test_set.identity:
            raise ValueError("manifest test-set identity does not match supplied test set")

        by_id = {sample.sample_id: sample for sample in test_set.samples}
        missing = [sample_id for sample_id in manifest.sample_ids if sample_id not in by_id]
        if missing:
            raise ValueError(f"manifest references unknown samples: {', '.join(missing)}")

        results = tuple(
            self._run_sample(sample=by_id[sample_id], manifest=manifest)
            for sample_id in manifest.sample_ids
        )
        return EvaluationReport(manifest=manifest, results=results)

    def _run_sample(
        self,
        *,
        sample: EvaluationSample,
        manifest: EvaluationRunManifest,
    ) -> EvaluationSampleResult:
        request = request_for_sample(
            sample,
            model=manifest.model,
            enable_thinking=(
                manifest.reasoning_profile.request_override
                if manifest.reasoning_profile is not None
                else None
            ),
        )
        started = time.perf_counter()
        try:
            result = self.executor.execute(request)
        except InferenceError as exc:
            elapsed = time.perf_counter() - started
            return EvaluationSampleResult(
                sample_id=sample.sample_id,
                succeeded=False,
                error_code=exc.code.value,
                metrics={"wall_time_seconds": elapsed},
            )
        except Exception:
            elapsed = time.perf_counter() - started
            return EvaluationSampleResult(
                sample_id=sample.sample_id,
                succeeded=False,
                error_code="executor_error",
                metrics={"wall_time_seconds": elapsed},
            )

        elapsed = time.perf_counter() - started
        scores: tuple[Score, ...] = tuple(
            scorer.score(sample, result) for scorer in self.scorers
        )
        metrics = dict(result.usage)
        metrics["wall_time_seconds"] = elapsed
        if manifest.runtime_fingerprint is not None:
            metrics["runtime_fingerprint"] = manifest.runtime_fingerprint
        return EvaluationSampleResult(
            sample_id=sample.sample_id,
            succeeded=True,
            scores=scores,
            metrics=metrics,
        )
