"""Built-in deterministic evaluation material for fast local model screening.

The starter set focuses on objective checks that do not require an LLM judge.
It is intentionally small enough for local iteration and versioned so results
remain comparable only within the same dataset version.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .core.contracts import InferenceResult, TaskType
from .evaluation import EvaluationSample, Score, TestSet


GENERAL_PURPOSE_V1 = TestSet(
    test_set_id="general-purpose",
    version="1.0.0",
    provenance={
        "source": "local-llm-server",
        "license": "repository-generated",
        "scoring": "deterministic-objective",
    },
    samples=(
        EvaluationSample("arith-001", TaskType.CHAT, {"input": "Return only the result of 17 + 28."}, {"exact": "45"}, ("arithmetic", "exact")),
        EvaluationSample("arith-002", TaskType.CHAT, {"input": "Return only the result of 12 * 9."}, {"exact": "108"}, ("arithmetic", "exact")),
        EvaluationSample("arith-003", TaskType.CHAT, {"input": "Return only the result of 144 / 12."}, {"exact": "12"}, ("arithmetic", "exact")),
        EvaluationSample("class-001", TaskType.CHAT, {"input": "Classify sentiment as positive, negative, or neutral: 'The update works exactly as expected.' Return one label only."}, {"exact_ci": "positive"}, ("classification",)),
        EvaluationSample("class-002", TaskType.CHAT, {"input": "Classify sentiment as positive, negative, or neutral: 'The app crashes whenever I open settings.' Return one label only."}, {"exact_ci": "negative"}, ("classification",)),
        EvaluationSample("class-003", TaskType.CHAT, {"input": "Classify sentiment as positive, negative, or neutral: 'The meeting is scheduled for Tuesday.' Return one label only."}, {"exact_ci": "neutral"}, ("classification",)),
        EvaluationSample("extract-001", TaskType.CHAT, {"input": "Extract only the email address: Contact Marta at marta@example.com for details."}, {"exact_ci": "marta@example.com"}, ("extraction",)),
        EvaluationSample("extract-002", TaskType.CHAT, {"input": "Extract only the date in YYYY-MM-DD format: The launch is on 7 October 2026."}, {"exact": "2026-10-07"}, ("extraction",)),
        EvaluationSample("extract-003", TaskType.CHAT, {"input": "Extract only the amount including currency symbol: The invoice total is €125.50."}, {"contains": ["€125.50"]}, ("extraction",)),
        EvaluationSample("follow-001", TaskType.CHAT, {"input": "Reply with exactly three words: local models matter"}, {"word_count": 3}, ("instruction",)),
        EvaluationSample("follow-002", TaskType.CHAT, {"input": "Return the word READY in uppercase and nothing else."}, {"exact": "READY"}, ("instruction", "exact")),
        EvaluationSample("follow-003", TaskType.CHAT, {"input": "Write exactly two comma-separated items: apple and pear."}, {"contains": ["apple", "pear"], "comma_count": 1}, ("instruction",)),
        EvaluationSample("reason-001", TaskType.CHAT, {"input": "A box has 5 red and 3 blue balls. How many balls total? Return only the number."}, {"exact": "8"}, ("reasoning", "exact")),
        EvaluationSample("reason-002", TaskType.CHAT, {"input": "If every zor is a mip and every mip is a taf, is every zor a taf? Answer yes or no only."}, {"exact_ci": "yes"}, ("reasoning",)),
        EvaluationSample("reason-003", TaskType.CHAT, {"input": "Which is larger: 0.8 or 0.75? Return only the larger number."}, {"exact": "0.8"}, ("reasoning", "exact")),
        EvaluationSample("json-001", TaskType.STRUCTURED_GENERATION, {"input": "Return JSON with keys name and age for Ada, age 36."}, {"json": {"name": "Ada", "age": 36}}, ("structured", "json")),
        EvaluationSample("json-002", TaskType.STRUCTURED_GENERATION, {"input": "Return JSON with key active set to true and count set to 3."}, {"json": {"active": True, "count": 3}}, ("structured", "json")),
        EvaluationSample("json-003", TaskType.STRUCTURED_GENERATION, {"input": "Return JSON with key colors containing red and blue in this order."}, {"json": {"colors": ["red", "blue"]}}, ("structured", "json")),
        EvaluationSample("format-001", TaskType.CHAT, {"input": "Return these numbers in ascending order separated by spaces only: 9 2 5 1"}, {"exact": "1 2 5 9"}, ("formatting", "exact")),
        EvaluationSample("format-002", TaskType.CHAT, {"input": "Return only a lowercase version of: LOCAL AI"}, {"exact": "local ai"}, ("formatting", "exact")),
    ),
)


@dataclass(frozen=True, slots=True)
class DeterministicObjectiveScorer:
    name: str = "deterministic_objective"

    def score(self, sample: EvaluationSample, result: InferenceResult) -> Score:
        content = result.content.strip()
        checks: list[bool] = []
        details: dict[str, object] = {}
        expected = sample.expected

        if "exact" in expected:
            passed = content == str(expected["exact"])
            checks.append(passed)
            details["exact"] = passed

        if "exact_ci" in expected:
            passed = content.casefold() == str(expected["exact_ci"]).strip().casefold()
            checks.append(passed)
            details["exact_ci"] = passed

        if "contains" in expected:
            required = [str(item) for item in expected["contains"]]
            passed = all(item.casefold() in content.casefold() for item in required)
            checks.append(passed)
            details["contains"] = passed

        if "word_count" in expected:
            count = len(re.findall(r"\S+", content))
            passed = count == int(expected["word_count"])
            checks.append(passed)
            details["word_count"] = count

        if "comma_count" in expected:
            count = content.count(",")
            passed = count == int(expected["comma_count"])
            checks.append(passed)
            details["comma_count"] = count

        if "json" in expected:
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = None
            passed = parsed == expected["json"]
            checks.append(passed)
            details["valid_expected_json"] = passed

        if not checks:
            return Score(self.name, None, passed=None, details={"reason": "no deterministic expectation"})

        passed_all = all(checks)
        return Score(
            self.name,
            1.0 if passed_all else 0.0,
            passed=passed_all,
            details=details,
        )
