"""Kiem tra pipeline/route quiz: co thuc su goi LLM va sinh cau hoi khong.

Hai lop test:
- Unit (stub LlmCaller, khong goi mang): kiem tra route/pipeline wiring va
  guardrail bang input gia lap, chay nhanh va deterministic trong CI.
- Integration (@pytest.mark.integration, tu dong skip khi thieu API key): goi
  LLM thuc, xac nhan cau hoi tra ve thuc su duoc SINH RA (khong phai du lieu
  tinh) - source_id phai tro ve dung chunk review_data, va noi dung khac nhau
  giua cac lan goi.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.pipelines.quiz import generate_quiz
from app.main import app
from app.schemas.quiz import QuizRequest

client = TestClient(app)

_HAS_LLM_KEY = bool(settings.openai_api_key or settings.gemini_api_key)


class _StubCaller:
    """LlmCaller gia lap - tra ve raw JSON co san, khong cham mang."""

    def __init__(self, raw: str) -> None:
        self._raw = raw
        self.calls = 0

    async def __call__(self, bundle, *, provider, timeout_s) -> str:  # noqa: ANN001
        self.calls += 1
        return self._raw


def _valid_quiz_json(source_ids: list[str]) -> str:
    items = []
    for i, source_id in enumerate(source_ids[:4]):
        items.append(
            {
                "prompt": f"Cau hoi so {i + 1} ve khai niem?",
                "options": ["Dap an A", "Dap an B", "Dap an C", "Dap an D"],
                "correct": i % 4,
                "whyCorrect": "Giai thich vi sao dap an nay dung, du dai.",
                "whyWrong": "Giai thich cach hieu sai pho bien, du dai.",
                "sourceId": source_id,
            }
        )
    return json.dumps({"items": items}, ensure_ascii=False)


def test_quiz_pipeline_returns_grounded_items_with_stub_llm() -> None:
    """Voi LLM tra du >=3 cau grounded dung source_id, pipeline phai giu lai."""
    from app.core.vector_search.retriever import get_review_topic_chunks

    chunk_ids = [c["source_id"] for c in get_review_topic_chunks("embedding")]
    assert len(chunk_ids) >= 3, "can it nhat 3 chunk de test co y nghia"

    stub = _StubCaller(_valid_quiz_json(chunk_ids))
    request = QuizRequest(topic="embedding", weak_points=[], difficulty="MEDIUM", num_items=4)

    envelope = asyncio.run(generate_quiz(request, request_id="test-1", call_llm=stub))

    assert envelope["success"] is True
    assert envelope["meta"]["degraded"] is False
    items = envelope["data"]["quiz"]
    assert len(items) >= 3
    assert stub.calls == 1, "khong duoc goi lai LLM khi lan dau da thanh cong"
    for item in items:
        assert item["sourceId"] in chunk_ids


def test_quiz_pipeline_degrades_when_llm_returns_too_few_items() -> None:
    """Guardrail G11 phai loai bo bo cau qua it, khong bia them cho du so luong."""
    from app.core.vector_search.retriever import get_review_topic_chunks

    chunk_ids = [c["source_id"] for c in get_review_topic_chunks("embedding")]
    only_one_item = json.dumps(
        {
            "items": [
                {
                    "prompt": "Chi mot cau?",
                    "options": ["A", "B", "C", "D"],
                    "correct": 0,
                    "whyCorrect": "Giai thich dung, du dai de qua guardrail.",
                    "whyWrong": "Giai thich sai, du dai de qua guardrail.",
                    "sourceId": chunk_ids[0],
                }
            ]
        },
        ensure_ascii=False,
    )
    stub = _StubCaller(only_one_item)
    request = QuizRequest(topic="embedding", weak_points=[], difficulty="MEDIUM", num_items=4)

    envelope = asyncio.run(generate_quiz(request, request_id="test-2", call_llm=stub))

    assert envelope["success"] is True
    assert envelope["meta"]["degraded"] is True
    assert envelope["meta"]["degraded_reason"] == "GUARDRAIL_QUIZ_INVALID"
    assert envelope["data"]["quiz"] == []


def test_quiz_pipeline_rejects_item_with_fabricated_source_id() -> None:
    """Cau hoi tro toi source_id khong ton tai trong chunk phai bi loai."""
    from app.core.vector_search.retriever import get_review_topic_chunks

    chunk_ids = [c["source_id"] for c in get_review_topic_chunks("embedding")]
    raw = _valid_quiz_json(chunk_ids[:2] + ["review:embedding:slide:bia-ra", "review:embedding:slide:bia-nua"])
    stub = _StubCaller(raw)
    request = QuizRequest(topic="embedding", weak_points=[], difficulty="MEDIUM", num_items=4)

    envelope = asyncio.run(generate_quiz(request, request_id="test-3", call_llm=stub))

    # Chi 2/4 cau hop le -> duoi nguong MIN_QUIZ_ITEMS=3 -> ha cap.
    assert envelope["meta"]["degraded"] is True
    assert envelope["data"]["quiz"] == []


def test_quiz_route_shape_with_stub_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kiem tra HTTP contract (/api/v1/quiz) khong phu thuoc LLM thuc."""
    from app.core.vector_search.retriever import get_review_topic_chunks

    chunk_ids = [c["source_id"] for c in get_review_topic_chunks("attention")]
    stub = _StubCaller(_valid_quiz_json(chunk_ids))
    monkeypatch.setattr("app.core.pipelines.quiz.default_llm_caller", stub)

    response = client.post(
        "/api/v1/quiz",
        json={"topic": "attention", "weak_points": [], "difficulty": "MEDIUM", "num_items": 4},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) >= 3
    for item in items:
        assert set(item.keys()) == {"id", "prompt", "options", "correct", "why", "topic", "source_id"}
        assert len(item["options"]) == 4
        assert 0 <= item["correct"] < 4
        assert item["topic"] == "attention"


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_LLM_KEY, reason="can OPENAI_API_KEY hoac GEMINI_API_KEY de goi LLM thuc")
def test_quiz_route_generates_distinct_real_items_per_call() -> None:
    """Xac nhan cau hoi la LLM SINH RA thuc su, khong phai fixture tinh:
    hai lan goi cho cung topic phai ra noi dung khac nhau, va source_id phai
    tro ve dung chunk trong review_data (khong the biet truoc neu la du lieu
    tinh vien san).
    """
    r1 = client.post(
        "/api/v1/quiz",
        json={"topic": "embedding", "weak_points": [], "difficulty": "MEDIUM", "num_items": 4},
    )
    r2 = client.post(
        "/api/v1/quiz",
        json={"topic": "embedding", "weak_points": ["nham token id voi embedding"], "difficulty": "HARD", "num_items": 4},
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    items1 = r1.json()["data"]["items"]
    items2 = r2.json()["data"]["items"]

    if not items1 or not items2:
        pytest.skip("LLM ha cap lan nay (timeout/It chunk) - xem test_quiz_pipeline_* de kiem guardrail")

    prompts1 = {item["prompt"] for item in items1}
    prompts2 = {item["prompt"] for item in items2}
    assert prompts1 != prompts2, "hai lan goi khac weak_points/difficulty phai ra cau hoi khac nhau"

    valid_source_ids = {c["source_id"] for c in __import__(
        "app.core.vector_search.retriever", fromlist=["get_review_topic_chunks"]
    ).get_review_topic_chunks("embedding")}
    for item in items1 + items2:
        assert item["source_id"] in valid_source_ids
