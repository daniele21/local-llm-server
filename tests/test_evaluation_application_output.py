from __future__ import annotations

from local_llm_server.core.capabilities import ThinkingMode
from local_llm_server.core.contracts import InferenceResult, TaskType, TerminationReason
from local_llm_server.evaluation import (
    EvaluationSample,
    SampleSelection,
    Score,
    TestSet,
    build_run_manifest,
)
from local_llm_server.evaluation_reasoning import (
    EvaluationReasoningPolicy,
    EvaluationReasoningProfile,
)
from local_llm_server.evaluation_runner import EvaluationRunner


class _Executor:
    def __init__(self, content: str) -> None:
        self.content = content

    def execute(self, request):
        return InferenceResult(
            task=request.task,
            model=request.model or "demo",
            content=self.content,
            termination_reason=TerminationReason.STOP,
        )


class _InspectingScorer:
    name = "inspect-normalized-output"

    def score(self, sample, result):
        assert result.content == '{"answer":42}'
        assert result.structured_output == {"answer": 42}
        assert result.metadata["reasoning_separated"] is True
        return Score(name=self.name, value=1.0, passed=True)


def _fixture():
    sample = EvaluationSample(
        "structured-1",
        TaskType.STRUCTURED_GENERATION,
        {"input": "return one JSON object"},
    )
    test_set = TestSet("structured-boundary", "1", (sample,))
    manifest = build_run_manifest(
        run_id="so2-evaluation",
        test_set=test_set,
        selection=SampleSelection(limit=1, seed=0),
        model="demo",
        reasoning_profile=EvaluationReasoningProfile(
            requested=EvaluationReasoningPolicy.ON,
            runtime_mode=ThinkingMode.SWITCHABLE,
            effective="on",
            request_override=True,
        ),
    )
    return test_set, manifest


def test_evaluation_scores_only_normalized_final_structured_output():
    test_set, manifest = _fixture()
    report = EvaluationRunner(
        _Executor('<think>private reasoning</think>{"answer":42}'),
        (_InspectingScorer(),),
    ).run(manifest=manifest, test_set=test_set)

    assert report.complete is True
    assert report.results[0].succeeded is True
    assert report.results[0].scores[0].passed is True


def test_evaluation_records_malformed_final_json_as_typed_sample_failure():
    test_set, manifest = _fixture()
    report = EvaluationRunner(
        _Executor("<think>private reasoning</think>not-json"),
        (_InspectingScorer(),),
    ).run(manifest=manifest, test_set=test_set)

    assert report.complete is True
    assert report.results[0].succeeded is False
    assert report.results[0].error_code == "invalid_model_output"
