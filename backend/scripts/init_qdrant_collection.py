import json
import os
import urllib.error
import urllib.request

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6663").rstrip("/")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "mistaketutor_sources")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIM", "768"))


def request(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{QDRANT_URL}{path}",
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


def create_collection() -> None:
    request(
        "PUT",
        f"/collections/{COLLECTION_NAME}",
        {
            "vectors": {
                "size": VECTOR_SIZE,
                "distance": "Cosine",
            }
        },
    )


def create_payload_indexes() -> None:
    indexes = {
        "source_id": "keyword",
        "source_type": "keyword",
        "module_slug": "keyword",
        "concept_slug": "keyword",
        "track": "keyword",
        "tags": "keyword",
        "created_at": "datetime",
    }
    for field_name, field_schema in indexes.items():
        request(
            "PUT",
            f"/collections/{COLLECTION_NAME}/index",
            {
                "field_name": field_name,
                "field_schema": field_schema,
            },
        )


def main() -> None:
    create_collection()
    create_payload_indexes()
    print(
        json.dumps(
            {
                "status": "ok",
                "qdrant_url": QDRANT_URL,
                "collection": COLLECTION_NAME,
                "vector_size": VECTOR_SIZE,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
