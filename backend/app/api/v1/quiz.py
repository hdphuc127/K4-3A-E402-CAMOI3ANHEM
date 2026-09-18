from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.pipelines.quiz import generate_quiz
from app.core.prompts import ERROR_CATALOG, ErrorCode
from app.schemas.common import ApiError, ApiResponse, ResponseMeta
from app.schemas.quiz import QuizItemOut, QuizRequest, QuizResult

router = APIRouter()


@router.post("/quiz", response_model=ApiResponse[QuizResult])
async def create_quiz(request: QuizRequest) -> ApiResponse[QuizResult] | JSONResponse:
    request_id = f"quiz-{uuid.uuid4().hex[:12]}"
    envelope = await generate_quiz(request, request_id=request_id)
    envelope_meta = envelope["meta"]
    meta = ResponseMeta(
        timestamp=envelope_meta["timestamp"],
        request_id=envelope_meta.get("request_id"),
        latency_ms=envelope_meta.get("latency_ms"),
    )

    if not envelope["success"]:
        error = envelope["error"] or {}
        response = ApiResponse[QuizResult](
            success=False,
            data=None,
            error=ApiError(**error),
            meta=meta,
        )
        try:
            status_code = ERROR_CATALOG[ErrorCode(error.get("code"))].http_status
        except ValueError:
            status_code = 500
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump(mode="json"),
        )

    data = envelope["data"] or {}
    raw_items: list[dict[str, Any]] = data.get("quiz", [])
    items = [
        QuizItemOut(
            id=f"{request_id}-{index}",
            prompt=str(item.get("prompt", "")),
            options=[str(o) for o in item.get("options", [])],
            correct=int(item.get("correct", 0)),
            why=str(item.get("whyCorrect", "")),
            topic=request.topic,
            source_id=str(item.get("sourceId", "")),
        )
        for index, item in enumerate(raw_items)
    ]
    result = QuizResult(quiz_id=request_id, difficulty=request.difficulty, items=items)
    return ApiResponse(success=True, data=result, error=None, meta=meta)
