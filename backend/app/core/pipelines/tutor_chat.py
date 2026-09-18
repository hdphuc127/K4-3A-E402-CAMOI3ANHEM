from __future__ import annotations

import time

from app.core.config import settings
from app.core.llm.client import default_llm_caller
from app.core.prompts import build_chat_prompt, run_guarded_generation
from app.core.prompts.schemas import LlmCaller, RetrievedChunk
from app.core.vector_search.retriever import (
    get_review_topic_context,
    resolve_review_topic,
    search_sources,
)
from app.schemas.chat import TutorChatRequest

_FIXTURE_RETRIEVAL_SCORE = 0.85
_MAX_HISTORY_TURNS = 6
_VECTOR_SEARCH_LIMIT = 6


async def answer_tutor_chat(
    request: TutorChatRequest,
    *,
    request_id: str,
    call_llm: LlmCaller | None = None,
) -> dict:
    """Answer an AI Tutor chat turn through the guarded RAG pipeline.

    Never raises: ``run_guarded_generation`` always returns a full envelope,
    matching the fallback ladder's "degrade, don't error" policy used
    elsewhere (see mistake_diagnosis.py).
    """
    topic = resolve_review_topic(request.text, request.context.topic)
    context = get_review_topic_context(topic) if topic else None

    chunks: list[RetrievedChunk] = []
    seen_source_ids: set[str] = set()

    if context is not None:
        chunks.append(
            RetrievedChunk(
                source_id=context["source_id"],
                title=context["title"],
                text=context["excerpt"],
                score=_FIXTURE_RETRIEVAL_SCORE,
            )
        )
        seen_source_ids.add(context["source_id"])

    # `get_review_topic_context` chỉ khớp được 4 chủ đề ôn tập cố định qua từ
    # khoá (xem `resolve_review_topic`). Với mọi câu hỏi khác — tức phần lớn
    # nội dung khoá học đã ingest vào Qdrant qua ingest_vlearn_pack.py — trước
    # đây không có gì được truy xuất cả, nên `chunks` rỗng và model buộc phải
    # từ chối dù tài liệu liên quan thực sự tồn tại. Luôn chạy thêm semantic
    # search trên toàn bộ kho slide/transcript để bù phần đó.
    try:
        vector_hits = search_sources(request.text, limit=_VECTOR_SEARCH_LIMIT)
    except Exception:  # noqa: BLE001 - Qdrant/embedding lỗi thì hạ cấp, không đánh sập lượt chat
        vector_hits = []

    for hit in vector_hits:
        source_id = hit["source_id"]
        if source_id in seen_source_ids:
            continue
        seen_source_ids.add(source_id)
        chunks.append(
            RetrievedChunk(
                source_id=source_id,
                title=hit["title"],
                text=hit["excerpt"],
                score=hit.get("score", 0.0),
            )
        )

    history = [
        (turn.role, turn.text) for turn in request.messages[-_MAX_HISTORY_TURNS:]
    ]

    bundle = build_chat_prompt(
        request.text,
        chunks,
        history=history,
        lesson_label=request.context.label,
        request_id=request_id,
    )

    return await run_guarded_generation(
        bundle,
        call_llm=call_llm or default_llm_caller,
        chunks=chunks,
        request_id=request_id,
        started_at=time.monotonic(),
        providers=(settings.llm_primary_provider, settings.llm_fallback_provider),
        deadline_s=settings.llm_deadline_s,
        enable_llm_judge=settings.enable_llm_judge,
    )
