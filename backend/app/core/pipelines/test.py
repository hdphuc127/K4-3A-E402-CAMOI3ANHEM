from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from app.core.pipelines.quiz import generate_quiz
from app.core.prompts.schemas import LlmCaller
from app.db.review_data import get_review_data
from app.schemas.quiz import QuizRequest

_ITEMS_REQUESTED_PER_TOPIC = 3
_ITEMS_KEPT_PER_TOPIC = 2


async def generate_diagnostic_test(
    week_id: str,
    *,
    request_id: str,
    call_llm: LlmCaller | None = None,
) -> dict:
    """Sinh bài kiểm tra nhanh đầu tuần bằng cùng pipeline LLM có guardrail
    dùng cho quiz thích ứng, thay vì bộ câu hỏi tĩnh cố định.

    Never raises: mỗi topic được sinh độc lập qua ``generate_quiz`` (đã tự
    degrade về rỗng khi lỗi/guardrail chặn) và chạy song song. Một topic thất
    bại chỉ làm bài test thiếu câu hỏi của topic đó, không làm hỏng cả bài.
    """
    started_at = time.monotonic()
    review_data = get_review_data()
    week = next((w for w in review_data.weeks if w.id == week_id), None)
    topics = list(week.topics) if week is not None else []

    async def _generate_for_topic(topic: str) -> list[dict[str, Any]]:
        envelope = await generate_quiz(
            QuizRequest(topic=topic, num_items=_ITEMS_REQUESTED_PER_TOPIC, difficulty="MEDIUM"),
            request_id=f"{request_id}-{topic}",
            call_llm=call_llm,
        )
        if not envelope.get("success"):
            return []
        raw_items = (envelope.get("data") or {}).get("quiz", [])
        kept = raw_items[:_ITEMS_KEPT_PER_TOPIC]
        for item in kept:
            item["topic"] = topic
        return kept

    results = await asyncio.gather(*(_generate_for_topic(topic) for topic in topics))
    items = [item for topic_items in results for item in topic_items]

    latency_ms = int((time.monotonic() - started_at) * 1000)
    return {
        "success": True,
        "data": {"items": items},
        "error": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "latency_ms": latency_ms,
            "degraded": len(items) < len(topics) * _ITEMS_KEPT_PER_TOPIC,
        },
    }
