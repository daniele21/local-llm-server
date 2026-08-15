"""Installable FastAPI routes for persisted evaluation history."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from .evaluation_history_service import EvaluationHistoryService


def install_evaluation_history_api(
    application: FastAPI,
    *,
    root: Path,
) -> FastAPI:
    """Install read-only evaluation history routes exactly once."""
    if getattr(application.state, "evaluation_history_api_installed", False):
        return application
    application.state.evaluation_history_api_installed = True
    service = EvaluationHistoryService(root)
    application.state.evaluation_history_service = service

    def list_history():
        return {"runs": [item.to_public_dict() for item in service.list_summaries()]}

    def get_history_run(run_id: str):
        try:
            return service.load_report(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="evaluation run not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def compare_history_runs(
        baseline: str = Query(..., min_length=1),
        candidate: str = Query(..., min_length=1),
    ):
        try:
            return service.compare(baseline, candidate).to_public_dict()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="evaluation run not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    application.add_api_route(
        "/api/v1/evaluation/history",
        list_history,
        methods=["GET"],
        tags=["Evaluation"],
        name="list_evaluation_history",
    )
    application.add_api_route(
        "/api/v1/evaluation/history/compare",
        compare_history_runs,
        methods=["GET"],
        tags=["Evaluation"],
        name="compare_evaluation_history",
    )
    application.add_api_route(
        "/api/v1/evaluation/history/{run_id}",
        get_history_run,
        methods=["GET"],
        tags=["Evaluation"],
        name="get_evaluation_history_run",
    )
    return application
