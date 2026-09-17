import json
import urllib.error
import urllib.request

from app.core.config import settings
from app.core.vector_search.embedding import embed_text
from app.db.review_data import get_review_data


def resolve_review_topic(text: str, context_topic: str | None = None) -> str | None:
    normalized = text.lower().replace("_", "-")
    topic_terms = {
        "embedding": ("embedding", "vector", "vector ngữ nghĩa"),
        "attention": ("attention", "trọng số chú ý", "tham chiếu đại từ"),
        "tool-calling": ("tool calling", "tool-calling", "gọi công cụ"),
        "tokenization": ("tokenizer", "tokenization", "token ID", "token"),
    }
    for topic, terms in topic_terms.items():
        if any(term in normalized for term in terms):
            return topic
    return context_topic


def get_review_topic_context(topic: str) -> dict[str, str] | None:
    review_data = get_review_data()
    lesson = review_data.lessons.get(topic)
    if lesson is None:
        return None
    body = "\n".join(
        paragraph
        for slide in lesson.slides
        for paragraph in slide.body
    )
    return {
        "source_id": f"review:{topic}",
        "title": lesson.lesson,
        "excerpt": body,
    }


def retrieve_tokenization_context(lesson_id: str, query: str | None = None) -> dict[str, str]:
    """Retrieve the best source chunk from Qdrant, with a local fallback."""

    search_text = f"{lesson_id}\n{query or ''}".strip()
    try:
        result = search_sources(search_text, limit=1)
    except Exception:  # noqa: BLE001 - keep MVP diagnosis available if Qdrant is down
        result = []
    if result:
        return result[0]
    fallback_sources = {
        "embedding": (
            "embedding:embedding-01",
            "Transcript - Embedding",
            "Embedding vector biểu diễn đặc trưng ngữ nghĩa của token trong không gian nhiều chiều.",
        ),
        "attention": (
            "attention:attention-01",
            "Transcript - Attention",
            "Attention tính trọng số liên quan giữa các token để quyết định thông tin nào ảnh hưởng tới đầu ra.",
        ),
        "tool-calling": (
            "tool-calling:tool-calling-01",
            "Transcript - Tool Calling",
            "Mô hình sinh ra lời gọi có cấu trúc và ứng dụng bên ngoài thực thi công cụ.",
        ),
    }
    source_id, title, excerpt = fallback_sources.get(
        lesson_id,
        (
            f"{lesson_id}:tokenization-03",
            "Transcript T06 - Tokenization",
            "Tokenization là bước chia văn bản thành các đơn vị nhỏ hơn để mô hình xử lý.",
        ),
    )
    return {"source_id": source_id, "title": title, "excerpt": excerpt}


def search_sources(query: str, *, limit: int = 4) -> list[dict[str, str]]:
    body = {
        "vector": embed_text(query),
        "limit": limit,
        "with_payload": True,
        "score_threshold": 0.05,
        "filter": {
            "must": [
                {"key": "source_pack", "match": {"value": "vlearn-pack"}},
            ]
        },
    }
    response = _request(
        "POST",
        f"/collections/{settings.qdrant_sources_collection}/points/search",
        body,
    )
    contexts = []
    for point in response.get("result", []):
        payload = point.get("payload", {})
        text = str(payload.get("text") or "")
        contexts.append(
            {
                "source_id": str(payload.get("source_id") or point.get("id")),
                "title": str(payload.get("title") or payload.get("source_path") or "VLearn source"),
                "excerpt": text[:800],
            }
        )
    return contexts


def _request(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{settings.qdrant_url.rstrip('/')}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_error = exc.read().decode("utf-8")
        raise RuntimeError(f"Qdrant error {exc.code}: {raw_error}") from exc
    return json.loads(raw) if raw else {}
