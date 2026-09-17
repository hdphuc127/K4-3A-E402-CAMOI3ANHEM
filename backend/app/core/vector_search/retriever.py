import json
import urllib.error
import urllib.request

from app.core.config import settings
from app.core.vector_search.embedding import embed_text


def retrieve_tokenization_context(lesson_id: str, query: str | None = None) -> dict[str, str]:
    """Retrieve the best source chunk from Qdrant, with a local fallback."""

    search_text = f"{lesson_id}\n{query or ''}".strip()
    try:
        result = search_sources(search_text, limit=1)
    except Exception:  # noqa: BLE001 - keep MVP diagnosis available if Qdrant is down
        result = []
    if result:
        return result[0]
    return {
        "source_id": f"{lesson_id}:tokenization-03",
        "title": "Transcript T06 - Tokenization",
        "excerpt": (
            "Tokenization la buoc chia van ban thanh cac don vi nho hon de "
            "mo hinh xu ly. Trong vi du don gian, ta co the tam tach theo "
            "khoang trang."
        ),
    }


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
