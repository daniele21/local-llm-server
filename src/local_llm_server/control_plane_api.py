"""Composable product/control-plane API routes outside the legacy server monolith."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from .core.contracts import ErrorCode, InferenceError
from .evaluation_service import (
    EvaluationRunRequest,
    EvaluationService,
    EvaluationStore,
    report_to_dict,
)
from .live_evidence import manager_evidence_payload
from .resource_policy import ResourcePolicySettings, resource_policy_snapshot
from .transcription import ResidentTranscriptionService, TranscriptionRequest

_MAX_TRANSCRIPTION_BYTES = 100 * 1024 * 1024


class EvaluationRunBody(BaseModel):
    model: str = Field(..., min_length=1)
    test_set_id: str = Field("general-purpose", min_length=1)
    sample_count: int = Field(20, ge=10)
    seed: int = 0


def install_product_api(
    application: FastAPI,
    *,
    evaluation_root: Path | None = None,
) -> FastAPI:
    """Install product routes exactly once after runtime configuration."""
    if getattr(application.state, "product_api_installed", False):
        return application
    application.state.product_api_installed = True

    root = evaluation_root or Path(
        os.getenv(
            "LOCAL_LLM_EVALUATION_DIR",
            str(Path.home() / ".local-llm-server" / "evaluations"),
        )
    )
    application.state.evaluation_store = EvaluationStore(root)

    async def transcribe_audio(
        request: Request,
        file: UploadFile = File(...),
        model: str = Form(...),
        language: str | None = Form(None),
        prompt: str | None = Form(None),
    ):
        audio = await file.read(_MAX_TRANSCRIPTION_BYTES + 1)
        if len(audio) > _MAX_TRANSCRIPTION_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "audio_too_large",
                    "max_bytes": _MAX_TRANSCRIPTION_BYTES,
                },
            )
        try:
            result = ResidentTranscriptionService(
                request.app.state.runtime_manager
            ).transcribe(
                TranscriptionRequest(
                    model=model,
                    audio=audio,
                    filename=file.filename,
                    language=language,
                    prompt=prompt,
                )
            )
        except InferenceError as exc:
            raise _http_error(exc) from exc
        return {
            "text": result.text,
            "model": result.model,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "segments": [dict(segment) for segment in result.segments],
        }

    application.add_api_route(
        "/v1/audio/transcriptions",
        transcribe_audio,
        methods=["POST"],
        tags=["Inference"],
        name="transcribe_audio",
    )

    settings = getattr(application.state, "settings", None)
    if not bool(getattr(settings, "enable_admin_api", False)):
        return application

    def get_resource_state(request: Request):
        policy_settings = getattr(
            request.app.state,
            "resource_policy_settings",
            ResourcePolicySettings(),
        )
        manager = request.app.state.runtime_manager
        return resource_policy_snapshot(policy_settings, manager.resource_manager)

    def get_evidence(request: Request):
        return manager_evidence_payload(request.app.state.runtime_manager)

    def list_test_sets(request: Request):
        service = EvaluationService(
            request.app.state.runtime_manager,
            store=request.app.state.evaluation_store,
        )
        return {"test_sets": list(service.list_test_sets())}

    def list_evaluation_runs(request: Request):
        store: EvaluationStore = request.app.state.evaluation_store
        return {"run_ids": list(store.list_run_ids())}

    def run_evaluation(body: EvaluationRunBody, request: Request):
        service = EvaluationService(
            request.app.state.runtime_manager,
            store=request.app.state.evaluation_store,
        )
        try:
            outcome = service.run(
                EvaluationRunRequest(
                    model=body.model,
                    test_set_id=body.test_set_id,
                    sample_count=body.sample_count,
                    seed=body.seed,
                )
            )
        except InferenceError as exc:
            raise _http_error(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "evidence_grade": outcome.evidence_grade,
            "report": report_to_dict(outcome.report),
        }

    application.add_api_route(
        "/api/v1/resources",
        get_resource_state,
        methods=["GET"],
        tags=["Resources"],
        name="get_resource_state",
    )
    application.add_api_route(
        "/api/v1/evidence",
        get_evidence,
        methods=["GET"],
        tags=["Observability"],
        name="get_runtime_evidence",
    )
    application.add_api_route(
        "/api/v1/evaluation/test-sets",
        list_test_sets,
        methods=["GET"],
        tags=["Evaluation"],
        name="list_evaluation_test_sets",
    )
    application.add_api_route(
        "/api/v1/evaluation/runs",
        list_evaluation_runs,
        methods=["GET"],
        tags=["Evaluation"],
        name="list_evaluation_runs",
    )
    application.add_api_route(
        "/api/v1/evaluation/runs",
        run_evaluation,
        methods=["POST"],
        tags=["Evaluation"],
        name="run_evaluation",
    )
    return application


def _http_error(error: InferenceError) -> HTTPException:
    status_code = 400
    if error.code is ErrorCode.MODEL_NOT_RESIDENT:
        status_code = 409
    elif error.code is ErrorCode.RESOURCE_EXHAUSTED:
        status_code = 429
    elif error.code is ErrorCode.TIMEOUT:
        status_code = 408
    return HTTPException(
        status_code=status_code,
        detail={
            "code": error.code.value,
            "message": error.message,
            "retryable": error.retryable,
            "details": dict(error.details),
        },
    )
