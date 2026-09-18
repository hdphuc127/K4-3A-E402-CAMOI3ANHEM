"""Kiem tra pipeline/route AI Tutor chat: grounded, mo rong kien thuc chung,
tu choi ngoai pham vi, streaming, va chong hallucination o duong tu choi.

Unit test dung stub LlmCaller (khong goi mang) de kiem guardrail deterministic.
Integration test (@pytest.mark.integration) goi LLM thuc, tu dong skip khi
thieu API key.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.pipelines.tutor_chat import answer_tutor_chat
from app.main import app
from app.schemas.chat import ChatContext, TutorChatRequest

client = TestClient(app)

_HAS_LLM_KEY = bool(settings.openai_api_key or settings.gemini_api_key)


class _StubCaller:
    def __init__(self, raw: str) -> None:
        self._raw = raw

    async def __call__(self, bundle, *, provider, timeout_s) -> str:  # noqa: ANN001
        return self._raw


def _answer_json(**overrides: object) -> str:
    base = {
        "answer": "Cau tra loi mac dinh.",
        "citations": [],
        "answerable": False,
        "injection_detected": False,
        "general_knowledge_used": False,
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


def test_grounded_answer_keeps_real_citation() -> None:
    from app.core.vector_search.retriever import get_review_topic_context

    context = get_review_topic_context("embedding")
    excerpt = context["excerpt"].split("\n")[0]
    raw = _answer_json(
        answer="Token ID la so thu tu trong tu dien.",
        citations=[{"source_id": context["source_id"], "excerpt": excerpt, "confidence": 0.9}],
        answerable=True,
    )
    stub = _StubCaller(raw)
    request = TutorChatRequest(
        text="Token ID la gi?", context=ChatContext(label="test", topic="embedding"), messages=[]
    )

    envelope = asyncio.run(answer_tutor_chat(request, request_id="t1", call_llm=stub))

    assert envelope["success"] is True
    assert envelope["meta"]["degraded"] is False
    assert len(envelope["data"]["citations"]) == 1
    assert envelope["data"]["citations"][0]["source_id"] == context["source_id"]


def test_general_knowledge_answer_gets_disclaimer_and_no_fake_citation() -> None:
    """Cau hoi ngoai tai lieu nhung dung linh vuc AI/LLM: khong tu choi cung,
    duoc mo rong bang kien thuc chung, nhung phai co disclaimer do CODE gan
    va khong duoc giu trich dan gia (source_id khong ton tai)."""
    raw = _answer_json(
        answer="RLHF la ky thuat huan luyen bang phan hoi cua con nguoi.",
        citations=[{"source_id": "bia-ra-khong-co-thuc", "excerpt": "abc", "confidence": 0.9}],
        answerable=False,
        general_knowledge_used=True,
    )
    stub = _StubCaller(raw)
    request = TutorChatRequest(
        text="RLHF la gi?", context=ChatContext(label="test", topic="embedding"), messages=[]
    )

    envelope = asyncio.run(answer_tutor_chat(request, request_id="t2", call_llm=stub))

    assert envelope["success"] is True
    assert envelope["meta"]["degraded"] is False
    answer_text = envelope["data"]["answer"]
    assert "RLHF" in answer_text
    assert "ngoài tài liệu" in answer_text  # disclaimer do code gan, khong phai model
    assert envelope["data"]["citations"] == []  # source_id bia phai bi loai


def test_off_topic_refusal_uses_deterministic_hint_not_model_text() -> None:
    """Model tu bia ten tai lieu/ky thuat khong ton tai trong refusal - guardrail
    G13 phai ghi de bang van ban xac dinh truoc, khong de lo hallucination ra
    ngoai (day la loi thuc te da gap: model bia ra "Memory injection")."""
    raw = _answer_json(
        answer=(
            "Mình không tìm thấy nội dung này trong tài liệu bài giảng của khóa học. "
            "Tài liệu hiện tại chỉ đề cập đến kỹ thuật Memory injection mà chưa giải thích."
        ),
        answerable=False,
        general_knowledge_used=False,
    )
    stub = _StubCaller(raw)
    request = TutorChatRequest(
        text="Token id la gi?", context=ChatContext(label="test", topic="tokenization"), messages=[]
    )

    envelope = asyncio.run(answer_tutor_chat(request, request_id="t3", call_llm=stub))

    answer_text = envelope["data"]["answer"]
    assert "Memory injection" not in answer_text
    assert "Bài 1 - Tokenization" in answer_text
    assert envelope["data"]["citations"] == []


def test_chat_route_shape_with_stub_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _answer_json(answer="Tra loi on dinh.", answerable=False, general_knowledge_used=False)
    stub = _StubCaller(raw)
    monkeypatch.setattr("app.core.pipelines.tutor_chat.default_llm_caller", stub)

    response = client.post(
        "/api/v1/chat",
        json={"text": "abc?", "context": {"label": "test", "topic": None}, "messages": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "text" in body["data"]
    assert "citations" in body["data"]


def test_chat_stream_route_emits_ndjson_delta_then_done(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _answer_json(
        answer="Cau tra loi du dai de co it nhat mot delta chunk trong stream.",
        answerable=False,
        general_knowledge_used=False,
    )
    stub = _StubCaller(raw)
    monkeypatch.setattr("app.core.pipelines.tutor_chat.default_llm_caller", stub)

    with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"text": "abc?", "context": {"label": "test", "topic": None}, "messages": []},
    ) as response:
        assert response.status_code == 200
        lines = [line for line in response.iter_lines() if line.strip()]

    events = [json.loads(line) for line in lines]
    assert events[-1]["type"] == "done"
    assert all(e["type"] in ("delta", "done") for e in events)
    assert "citations" in events[-1]
    assert "degraded" in events[-1]


@pytest.mark.integration
@pytest.mark.skipif(not _HAS_LLM_KEY, reason="can OPENAI_API_KEY hoac GEMINI_API_KEY de goi LLM thuc")
def test_chat_route_distinguishes_grounded_expansion_and_offtopic_with_real_llm() -> None:
    grounded = client.post(
        "/api/v1/chat",
        json={
            "text": "Embedding vector la gi?",
            "context": {"label": "test", "topic": "embedding"},
            "messages": [],
        },
    ).json()["data"]["text"]
    assert grounded.strip()

    off_topic = client.post(
        "/api/v1/chat",
        json={
            "text": "Cong thuc nau pho bo the nao?",
            "context": {"label": "test", "topic": None},
            "messages": [],
        },
    ).json()["data"]["text"]
    assert "phở" not in off_topic.lower()
