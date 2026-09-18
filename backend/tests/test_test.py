"""Kiem tra pipeline/route bai kiem tra nhanh dau tuan (sinh bang LLM).

Tuong tu tests/test_quiz.py: dung stub LlmCaller de kiem tra wiring/guardrail
khong goi mang, deterministic trong CI.
"""

from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient

from app.core.pipelines.test import generate_diagnostic_test
from app.core.vector_search.retriever import get_review_topic_chunks
from app.main import app

client = TestClient(app)


class _StubCaller:
    """LlmCaller gia lap, tra ve raw JSON co san theo topic cua bundle."""

    def __init__(self, raw_by_topic: dict[str, str] | None = None, default_raw: str | None = None) -> None:
        self._raw_by_topic = raw_by_topic or {}
        self._default_raw = default_raw
        self.calls: list[str] = []

    async def __call__(self, bundle, *, provider, timeout_s) -> str:  # noqa: ANN001
        topic = bundle.user.split("<topic>\n")[1].split("\n")[0] if "<topic>" in bundle.user else ""
        self.calls.append(topic)
        if topic in self._raw_by_topic:
            return self._raw_by_topic[topic]
        if self._default_raw is not None:
            return self._default_raw
        raise AssertionError(f"No stub response configured for topic {topic!r}")


def _valid_quiz_json(source_ids: list[str]) -> str:
    items = []
    for i, source_id in enumerate(source_ids[:3]):
        items.append(
            {
                "prompt": f"Cau hoi so {i + 1}?",
                "options": ["Dap an A", "Dap an B", "Dap an C", "Dap an D"],
                "correct": i % 4,
                "whyCorrect": "Giai thich vi sao dap an nay dung, du dai de qua guardrail.",
                "whyWrong": "Giai thich cach hieu sai pho bien, du dai de qua guardrail.",
                "sourceId": source_id,
            }
        )
    return json.dumps({"items": items}, ensure_ascii=False)


def _empty_quiz_json() -> str:
    return json.dumps({"items": []}, ensure_ascii=False)


def test_diagnostic_test_merges_items_across_all_week_topics() -> None:
    """Tuan w2 co 4 topic; moi topic sinh duoc cau hoi thi bai test phai gop du."""
    raw_by_topic = {
        topic: _valid_quiz_json([c["source_id"] for c in get_review_topic_chunks(topic)])
        for topic in ("tokenization", "embedding", "attention", "tool-calling")
    }
    stub = _StubCaller(raw_by_topic=raw_by_topic)

    envelope = asyncio.run(generate_diagnostic_test("w2", request_id="test-diag-1", call_llm=stub))

    assert envelope["success"] is True
    items = envelope["data"]["items"]
    assert len(items) == 8, "4 topic x toi da 2 cau/topic"
    topics_seen = {item["topic"] for item in items}
    assert topics_seen == {"tokenization", "embedding", "attention", "tool-calling"}


def test_diagnostic_test_degrades_partially_when_one_topic_fails() -> None:
    """Mot topic khong sinh duoc cau hoi khong duoc lam hong cac topic con lai."""
    raw_by_topic = {
        "tokenization": _valid_quiz_json([c["source_id"] for c in get_review_topic_chunks("tokenization")]),
        "embedding": _empty_quiz_json(),
        "attention": _valid_quiz_json([c["source_id"] for c in get_review_topic_chunks("attention")]),
        "tool-calling": _valid_quiz_json([c["source_id"] for c in get_review_topic_chunks("tool-calling")]),
    }
    stub = _StubCaller(raw_by_topic=raw_by_topic)

    envelope = asyncio.run(generate_diagnostic_test("w2", request_id="test-diag-2", call_llm=stub))

    assert envelope["success"] is True
    items = envelope["data"]["items"]
    topics_seen = {item["topic"] for item in items}
    assert topics_seen == {"tokenization", "attention", "tool-calling"}
    assert envelope["meta"]["degraded"] is True


def test_test_route_shape_with_stub_llm(monkeypatch) -> None:
    """Kiem tra HTTP contract (/api/v1/test) khong phu thuoc LLM thuc."""
    raw_by_topic = {
        topic: _valid_quiz_json([c["source_id"] for c in get_review_topic_chunks(topic)])
        for topic in ("tokenization", "embedding", "attention", "tool-calling")
    }
    stub = _StubCaller(raw_by_topic=raw_by_topic)
    monkeypatch.setattr("app.core.pipelines.quiz.default_llm_caller", stub)

    response = client.post("/api/v1/test", json={"week_id": "w2"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert len(items) == 8
    for item in items:
        assert set(item.keys()) == {
            "id",
            "prompt",
            "options",
            "correct",
            "why",
            "misconception",
            "topic",
            "source_id",
        }
        assert len(item["options"]) == 4
        assert 0 <= item["correct"] < 4
