from __future__ import annotations

import pytest

from local_llm_server.core.contracts import TaskType
from local_llm_server.evaluation import (
    EvaluationReport,
    EvaluationSample,
    EvaluationSampleResult,
    SampleSelection,
    TestSet,
    build_run_manifest,
)


def _test_set() -> TestSet:
    return TestSet(
        test_set_id="general-v1",
        version="1.0.0",
        samples=tuple(
            EvaluationSample(
                sample_id=f"sample-{index:02d}",
                task=TaskType.CHAT,
                payload={"input": f"question {index}"},
            )
            for index in range(10)
        ),
        provenance={"source": "built-in"},
    )


def test_sample_selection_is_deterministic_for_seed():
    test_set = _test_set()
    selection = SampleSelection(limit=4, seed=7)

    first = tuple(sample.sample_id for sample in selection.select(test_set))
    second = tuple(sample.sample_id for sample in selection.select(test_set))

    assert first == second
    assert len(first) == 4


def test_different_seed_can_change_selected_subset():
    test_set = _test_set()
    first = tuple(sample.sample_id for sample in SampleSelection(limit=4, seed=1).select(test_set))
    second = tuple(sample.sample_id for sample in SampleSelection(limit=4, seed=2).select(test_set))
    assert first != second


def test_duplicate_sample_ids_are_rejected():
    sample = EvaluationSample("same", TaskType.CHAT, {"input": "hello"})
    with pytest.raises(ValueError, match="unique"):
        TestSet("duplicate", "1", (sample, sample))


def test_manifest_records_exact_test_set_selection_identity():
    test_set = _test_set()
    manifest = build_run_manifest(
        run_id="run-1",
        test_set=test_set,
        selection=SampleSelection(limit=3, seed=11),
        model="demo-model",
    )

    assert manifest.test_set_identity == test_set.identity
    assert len(manifest.sample_ids) == 3
    assert manifest.runtime_fingerprint is None
    assert manifest.task_types == (TaskType.CHAT,)


def test_report_is_complete_only_for_exact_manifest_samples():
    test_set = _test_set()
    manifest = build_run_manifest(
        run_id="run-2",
        test_set=test_set,
        selection=SampleSelection(limit=2, seed=3),
        model="demo-model",
    )
    complete = EvaluationReport(
        manifest,
        tuple(EvaluationSampleResult(sample_id, True) for sample_id in manifest.sample_ids),
    )
    incomplete = EvaluationReport(
        manifest,
        (EvaluationSampleResult(manifest.sample_ids[0], True),),
    )

    assert complete.complete is True
    assert incomplete.complete is False
