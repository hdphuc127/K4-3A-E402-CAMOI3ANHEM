from __future__ import annotations

import time

from app.core.config import settings
from app.core.llm.client import default_llm_caller
from app.core.prompts import build_quiz_prompt, run_guarded_generation
from app.core.prompts.schemas import LlmCaller, RetrievedChunk
from app.core.vector_search.retriever import get_review_topic_chunks
from app.schemas.quiz import QuizRequest

_FIXTURE_RETRIEVAL_SCORE = 0.9


async def generate_quiz(
    request: QuizRequest,
    *,
    request_id: str,
    call_llm: LlmCaller | None = None,
) -> dict:
    """Generate an adaptive quiz through the guarded RAG pipeline.

    Never raises: mirrors ``answer_tutor_chat`` — on any failure or missing
    context the fallback ladder degrades to an envelope with an empty
    ``quiz`` list instead of raising, and the route renders that as "quiz
    not ready" rather than a 500.

    Uses one chunk per lesson slide/static question instead of a single
    chunk for the whole topic: every quiz item needs its own real
    ``source_id`` (guardrail G11), so it can only ground as many distinct
    items as there are distinct chunks.
    """
    chunks: list[RetrievedChunk] = [
        RetrievedChunk(
            source_id=raw["source_id"],
            title=raw["title"],
            text=raw["excerpt"],
            score=_FIXTURE_RETRIEVAL_SCORE,
        )
        for raw in get_review_topic_chunks(request.topic)
    ]

    bundle = build_quiz_prompt(
        request.topic,
        chunks,
        num_items=request.num_items,
        weak_points=request.weak_points,
        difficulty=request.difficulty,
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
