from __future__ import annotations

from local_llm_server.core.contracts import InferenceResult, TaskType, TerminationReason
from local_llm_server.evaluation_builtin import (
    DeterministicObjectiveScorer,
    GENERAL_PURPOSE_V1,
)


def _result(content: str, task: TaskType = TaskType.CHAT) -> InferenceResult:
    return InferenceResult(
        task=task,
        model="demo",
        content=content,
        termination_reason=TerminationReason.STOP,
    )


def test_general_purpose_set_has_twenty_stable_samples():
    assert GENERAL_PURPOSE_V1.test_set_id == "general-purpose"
    assert GENERAL_PURPOSE_V1.version == "1.0.0"
    assert len(GENERAL_PURPOSE_V1.samples) == 20
    assert len({sample.sample_id for sample in GENERAL_PURPOSE_V1.samples}) == 20


def test_general_purpose_set_covers_multiple_objective_categories():
    tags = {tag for sample in GENERAL_PURPOSE_V1.samples for tag in sample.tags}
    assert {"arithmetic", "classification", "extraction", "instruction", "reasoning", "structured", "formatting"}.issubset(tags)


def test_exact_and_case_insensitive_scoring():
    scorer = DeterministicObjectiveScorer()
    exact = next(sample for sample in GENERAL_PURPOSE_V1.samples if sample.sample_id == "arith-001")
    classification = next(sample for sample in GENERAL_PURPOSE_V1.samples if sample.sample_id == "class-001")

    assert scorer.score(exact, _result("45")).passed is True
    assert scorer.score(exact, _result("The answer is 45")).passed is False
    assert scorer.score(classification, _result("POSITIVE")).passed is True


def test_json_scoring_requires_exact_expected_structure():
    scorer = DeterministicObjectiveScorer()
    sample = next(sample for sample in GENERAL_PURPOSE_V1.samples if sample.sample_id == "json-001")

    assert scorer.score(sample, _result('{"name":"Ada","age":36}', TaskType.STRUCTURED_GENERATION)).passed is True
    assert scorer.score(sample, _result('{"name":"Ada","age":"36"}', TaskType.STRUCTURED_GENERATION)).passed is False


def test_instruction_constraints_can_combine_checks():
    scorer = DeterministicObjectiveScorer()
    sample = next(sample for sample in GENERAL_PURPOSE_V1.samples if sample.sample_id == "follow-003")

    assert scorer.score(sample, _result("apple, pear")).passed is True
    assert scorer.score(sample, _result("apple pear")).passed is False
