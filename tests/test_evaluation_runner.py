from local_llm_server.core.capabilities import ThinkingMode
from local_llm_server.core.contracts import (
    ErrorCode,
    InferenceError,
    InferenceResult,
    TaskType,
    TerminationReason,
)
from local_llm_server.evaluation import SampleSelection, build_run_manifest
from local_llm_server.evaluation_builtin import (
    DeterministicObjectiveScorer,
    GENERAL_PURPOSE_V1,
)
from local_llm_server.evaluation_reasoning import (
    EvaluationReasoningPolicy,
    EvaluationReasoningProfile,
)
from local_llm_server.evaluation_runner import EvaluationRunner, request_for_sample


class FakeExecutor:
    def __init__(self, outputs):
        self.outputs = outputs
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        output = self.outputs[request.metadata["evaluation_sample_id"]]
        if isinstance(output, Exception):
            raise output
        return InferenceResult(
            task=request.task,
            model=request.model or "missing",
            content=output,
            termination_reason=TerminationReason.STOP,
            usage={"output_tokens": 1},
        )


def test_request_for_structured_sample_requests_json_object():
    sample = next(sample for sample in GENERAL_PURPOSE_V1.samples if sample.sample_id == "json-001")
    request = request_for_sample(sample, model="demo")
    assert request.task is TaskType.STRUCTURED_GENERATION
    assert request.output.format == "json_object"
    assert request.generation.temperature == 0.0
    assert request.metadata["evaluation_sample_id"] == "json-001"


def test_request_for_sample_accepts_explicit_reasoning_off():
    sample = GENERAL_PURPOSE_V1.samples[0]
    request = request_for_sample(sample, model="demo", enable_thinking=False)
    assert request.generation.enable_thinking is False


def test_runner_executes_selected_samples_scores_and_carries_fingerprint_and_reasoning_policy():
    selection = SampleSelection(limit=2, seed=7)
    selected = selection.select(GENERAL_PURPOSE_V1)
    outputs = {}
    for sample in selected:
        expected = sample.expected
        if "exact" in expected:
            outputs[sample.sample_id] = str(expected["exact"])
        elif "exact_ci" in expected:
            outputs[sample.sample_id] = str(expected["exact_ci"])
        elif "json" in expected:
            import json
            outputs[sample.sample_id] = json.dumps(expected["json"])
        elif "contains" in expected:
            outputs[sample.sample_id] = ", ".join(str(v) for v in expected["contains"])
        else:
            outputs[sample.sample_id] = "local models matter"

    manifest = build_run_manifest(
        run_id="run-1",
        test_set=GENERAL_PURPOSE_V1,
        selection=selection,
        model="demo-model",
        runtime_fingerprint="fp-123",
        reasoning_profile=EvaluationReasoningProfile(
            requested=EvaluationReasoningPolicy.OFF,
            runtime_mode=ThinkingMode.SWITCHABLE,
            effective="off",
            request_override=False,
        ),
    )
    executor = FakeExecutor(outputs)
    report = EvaluationRunner(executor, (DeterministicObjectiveScorer(),)).run(
        manifest=manifest,
        test_set=GENERAL_PURPOSE_V1,
    )

    assert report.complete is True
    assert len(executor.requests) == 2
    assert all(request.generation.enable_thinking is False for request in executor.requests)
    assert all(result.succeeded for result in report.results)
    assert all(result.metrics["runtime_fingerprint"] == "fp-123" for result in report.results)
    assert all(result.metrics["output_tokens"] == 1 for result in report.results)
    assert [result.input_text for result in report.results] == [
        sample.payload["input"] for sample in selected
    ]
    assert [dict(result.expected) for result in report.results] == [
        dict(sample.expected) for sample in selected
    ]
    assert [result.output_text for result in report.results] == [
        outputs[sample.sample_id] for sample in selected
    ]


def test_runner_records_typed_inference_error_without_aborting_run():
    sample = GENERAL_PURPOSE_V1.samples[0]
    selection = SampleSelection(limit=1, seed=0)
    # Build a one-sample test set to keep the manifest deterministic for this case.
    from local_llm_server.evaluation import TestSet
    test_set = TestSet("one", "1", (sample,))
    manifest = build_run_manifest(
        run_id="run-error",
        test_set=test_set,
        selection=selection,
        model="demo",
    )
    executor = FakeExecutor({
        sample.sample_id: InferenceError(ErrorCode.TIMEOUT, "timed out", retryable=True)
    })
    report = EvaluationRunner(executor, (DeterministicObjectiveScorer(),)).run(
        manifest=manifest,
        test_set=test_set,
    )

    assert report.complete is True
    assert report.results[0].succeeded is False
    assert report.results[0].error_code == "timeout"
    assert report.results[0].input_text == sample.payload["input"]
    assert dict(report.results[0].expected) == dict(sample.expected)
    assert report.results[0].output_text is None


def test_runner_rejects_manifest_for_different_test_set_identity():
    selection = SampleSelection(limit=1, seed=0)
    manifest = build_run_manifest(
        run_id="run-mismatch",
        test_set=GENERAL_PURPOSE_V1,
        selection=selection,
        model="demo",
    )
    from local_llm_server.evaluation import EvaluationSample, TestSet
    other = TestSet(
        "general-purpose",
        "1.0.0",
        (EvaluationSample("other", TaskType.CHAT, {"input": "x"}),),
    )
    executor = FakeExecutor({})
    try:
        EvaluationRunner(executor, ()).run(manifest=manifest, test_set=other)
    except ValueError as exc:
        assert "identity" in str(exc)
    else:
        raise AssertionError("expected manifest/test-set identity mismatch")
