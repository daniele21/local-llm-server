"""Load persisted evaluation reports and expose compatibility-aware history."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .evaluation import TestSet

from .evaluation_history import (
    EvaluationComparison,
    EvaluationRunSummary,
    compare_run_summaries,
    summarize_report_payload,
)


@dataclass(frozen=True, slots=True)
class StoredRunSummary:
    summary: EvaluationRunSummary
    stored_at: float

    def to_public_dict(self) -> dict[str, object]:
        payload = self.summary.to_public_dict()
        payload["stored_at"] = self.stored_at
        return payload


class EvaluationHistoryService:
    """Read-only history/index layer over the immutable JSON run store."""

    def __init__(
        self,
        root: Path,
        *,
        test_set_resolver: Callable[[str, str | None], TestSet | None] | None = None,
    ) -> None:
        self.root = root.expanduser()
        self.test_set_resolver = test_set_resolver

    def list_summaries(self) -> tuple[StoredRunSummary, ...]:
        if not self.root.exists():
            return ()
        summaries: list[StoredRunSummary] = []
        for path in self.root.glob("*.json"):
            if not path.is_file():
                continue
            try:
                payload = self._load_path(path)
                summary = summarize_report_payload(payload)
            except (OSError, ValueError, json.JSONDecodeError, TypeError):
                # A corrupt/foreign file must not make all history unavailable.
                continue
            summaries.append(
                StoredRunSummary(summary=summary, stored_at=path.stat().st_mtime)
            )
        return tuple(
            sorted(summaries, key=lambda item: (item.stored_at, item.summary.run_id), reverse=True)
        )

    def load_report(self, run_id: str) -> dict[str, Any]:
        path = self._path_for_run(run_id)
        if not path.is_file():
            raise FileNotFoundError(run_id)
        payload = self._load_path(path)
        manifest = payload.get("manifest")
        if not isinstance(manifest, Mapping) or manifest.get("run_id") != run_id:
            raise ValueError("stored report run_id does not match requested run")
        return self._attach_dataset_context(payload)

    def get_summary(self, run_id: str) -> EvaluationRunSummary:
        return summarize_report_payload(self.load_report(run_id))

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> EvaluationComparison:
        if baseline_run_id == candidate_run_id:
            raise ValueError("baseline and candidate run IDs must differ")
        return compare_run_summaries(
            self.get_summary(baseline_run_id),
            self.get_summary(candidate_run_id),
        )

    def _path_for_run(self, run_id: str) -> Path:
        if not run_id or not all(ch.isalnum() or ch in {"-", "_"} for ch in run_id):
            raise ValueError("invalid run_id")
        path = (self.root / f"{run_id}.json").resolve()
        root = self.root.resolve()
        if root != path.parent:
            raise ValueError("invalid run_id path")
        return path

    @staticmethod
    def _load_path(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("evaluation report must be a JSON object")
        return payload

    def _attach_dataset_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        manifest = payload.get("manifest")
        if not isinstance(manifest, Mapping) or self.test_set_resolver is None:
            payload["dataset_context"] = {"status": "unavailable"}
            return payload

        test_set_id = manifest.get("test_set_id")
        version = manifest.get("test_set_version")
        if not isinstance(test_set_id, str) or not isinstance(version, str):
            payload["dataset_context"] = {"status": "unavailable"}
            return payload

        try:
            test_set = self.test_set_resolver(test_set_id, version)
        except (OSError, ValueError):
            test_set = None
        if test_set is None:
            payload["dataset_context"] = {"status": "dataset_missing"}
            return payload
        if manifest.get("test_set_identity") != test_set.identity:
            payload["dataset_context"] = {"status": "identity_mismatch"}
            return payload

        samples = {sample.sample_id: sample for sample in test_set.samples}
        recovered = 0
        results = payload.get("results")
        if isinstance(results, list):
            for result in results:
                if not isinstance(result, dict):
                    continue
                sample = samples.get(result.get("sample_id"))
                if sample is None:
                    continue
                current = result.get("content")
                content = dict(current) if isinstance(current, Mapping) else {}
                if "input" not in content:
                    content["input"] = sample.payload.get("input")
                if "expected" not in content:
                    content["expected"] = dict(sample.expected)
                result["content"] = content
                recovered += 1
        payload["dataset_context"] = {
            "status": "matched",
            "sample_context_count": recovered,
        }
        return payload
