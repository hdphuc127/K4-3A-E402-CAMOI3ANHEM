from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.pipelines.test import generate_diagnostic_test
from app.core.prompts import ERROR_CATALOG, ErrorCode
from app.schemas.common import ApiError, ApiResponse, ResponseMeta
from app.schemas.test import TestItemOut, TestRequest, TestResult

router = APIRouter()


@router.post("/test", response_model=ApiResponse[TestResult])
async def create_test(request: TestRequest) -> ApiResponse[TestResult] | JSONResponse:
    request_id = f"test-{uuid.uuid4().hex[:12]}"
    envelope = await generate_diagnostic_test(request.week_id, request_id=request_id)
    envelope_meta = envelope["meta"]
    meta = ResponseMeta(
        timestamp=envelope_meta["timestamp"],
        request_id=envelope_meta.get("request_id"),
        latency_ms=envelope_meta.get("latency_ms"),
    )

    if not envelope["success"]:
        error = envelope["error"] or {}
        response = ApiResponse[TestResult](
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
    raw_items: list[dict[str, Any]] = data.get("items", [])
    items = [
        TestItemOut(
            id=f"{request_id}-{index}",
            prompt=str(item.get("prompt", "")),
            options=[str(o) for o in item.get("options", [])],
            correct=int(item.get("correct", 0)),
            why=str(item.get("whyCorrect", "")),
            misconception=str(item.get("whyWrong", "")),
            topic=str(item.get("topic", "")),
            source_id=str(item.get("sourceId", "")),
        )
        for index, item in enumerate(raw_items)
    ]
    result = TestResult(test_id=request_id, items=items)
    return ApiResponse(success=True, data=result, error=None, meta=meta)
