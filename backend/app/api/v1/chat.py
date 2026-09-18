from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.pipelines.tutor_chat import answer_tutor_chat
from app.core.prompts import ERROR_CATALOG, ErrorCode
from app.schemas.chat import ChatResult, TutorChatRequest
from app.schemas.common import ApiError, ApiResponse, ResponseMeta
from app.schemas.diagnosis import SourceCitation

router = APIRouter()

# NDJSON delta size for the simulated token stream: guardrails need the full
# parsed+validated answer before anything can be sent, so "streaming" here
# means chunking the already-validated text rather than proxying provider
# tokens live.
_STREAM_CHUNK_CHARS = 40


def _response_meta(envelope: dict[str, Any]) -> ResponseMeta:
    envelope_meta = envelope["meta"]
    return ResponseMeta(
        timestamp=envelope_meta["timestamp"],
        request_id=envelope_meta.get("request_id"),
        latency_ms=envelope_meta.get("latency_ms"),
    )


def _error_status(error: dict[str, Any]) -> int:
    try:
        return ERROR_CATALOG[ErrorCode(error.get("code"))].http_status
    except ValueError:
        return 500


@router.post("/chat", response_model=ApiResponse[ChatResult])
async def create_chat_reply(
    request: TutorChatRequest,
) -> ApiResponse[ChatResult] | JSONResponse:
    request_id = f"chat-{uuid.uuid4().hex[:12]}"
    envelope = await answer_tutor_chat(request, request_id=request_id)
    meta = _response_meta(envelope)

    if not envelope["success"]:
        error = envelope["error"] or {}
        response = ApiResponse[ChatResult](
            success=False,
            data=None,
            error=ApiError(**error),
            meta=meta,
        )
        return JSONResponse(
            status_code=_error_status(error),
            content=response.model_dump(mode="json"),
        )

    data = envelope["data"] or {}
    result = ChatResult(
        text=str(data.get("answer", "")),
        citations=[SourceCitation(**c) for c in data.get("citations", [])],
    )
    return ApiResponse(success=True, data=result, error=None, meta=meta)


@router.post("/chat/stream")
async def create_chat_reply_stream(request: TutorChatRequest) -> StreamingResponse:
    request_id = f"chat-{uuid.uuid4().hex[:12]}"
    envelope = await answer_tutor_chat(request, request_id=request_id)

    async def event_stream() -> AsyncIterator[bytes]:
        if not envelope["success"]:
            yield _ndjson_line(
                {"type": "done", "text": "", "citations": [], "degraded": True}
            )
            return

        data = envelope["data"] or {}
        answer = str(data.get("answer", ""))
        citations = data.get("citations", [])
        degraded = bool(envelope["meta"].get("degraded", False))

        for start in range(0, len(answer), _STREAM_CHUNK_CHARS):
            chunk = answer[start : start + _STREAM_CHUNK_CHARS]
            yield _ndjson_line({"type": "delta", "text": chunk})

        yield _ndjson_line(
            {"type": "done", "citations": citations, "degraded": degraded}
        )

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


def _ndjson_line(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
