import json
import os
import urllib.error
import urllib.request

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6663").rstrip("/")
VECTOR_SIZE = int(os.getenv("EMBEDDING_DIM", "768"))

COLLECTIONS = {
    os.getenv("QDRANT_SOURCES_COLLECTION", "mistaketutor_sources"): {
        "description": "Transcript, slide, rubric, and fixture chunks used as citation sources.",
        "indexes": {
            "source_id": "keyword",
            "source_type": "keyword",
            "module_slug": "keyword",
            "concept_slug": "keyword",
            "track": "keyword",
            "tags": "keyword",
            "created_at": "datetime",
        },
    },
    os.getenv("QDRANT_EXPLANATIONS_COLLECTION", "mistaketutor_explanations"): {
        "description": "Learner teach-back explanations for similarity and gap analysis.",
        "indexes": {
            "user_id": "integer",
            "session_id": "integer",
            "attempt_id": "integer",
            "module_slug": "keyword",
            "concept_slug": "keyword",
            "attempt_no": "integer",
            "created_at": "datetime",
        },
    },
    os.getenv("QDRANT_GAP_DIAGNOSES_COLLECTION", "mistaketutor_gap_diagnoses"): {
        "description": "AI gap diagnosis outputs and follow-up questions.",
        "indexes": {
            "user_id": "integer",
            "session_id": "integer",
            "attempt_id": "integer",
            "concept_slug": "keyword",
            "gap_type": "keyword",
            "severity": "keyword",
            "source_id": "keyword",
            "created_at": "datetime",
        },
    },
    os.getenv("QDRANT_EVAL_CASES_COLLECTION", "mistaketutor_eval_cases"): {
        "description": "Golden-set and hard-test cases for CP3/CP4 evaluation.",
        "indexes": {
            "case_id": "keyword",
            "case_type": "keyword",
            "module_slug": "keyword",
            "concept_slug": "keyword",
            "expected_gap_type": "keyword",
            "difficulty": "keyword",
            "split": "keyword",
            "created_at": "datetime",
        },
    },
}


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


def create_collection(collection_name: str) -> None:
    request(
        "PUT",
        f"/collections/{collection_name}",
        {
            "vectors": {
                "size": VECTOR_SIZE,
                "distance": "Cosine",
            }
        },
    )


def create_payload_indexes(collection_name: str, indexes: dict[str, str]) -> None:
    for field_name, field_schema in indexes.items():
        request(
            "PUT",
            f"/collections/{collection_name}/index",
            {
                "field_name": field_name,
                "field_schema": field_schema,
            },
        )


def main() -> None:
    created = []
    for collection_name, config in COLLECTIONS.items():
        create_collection(collection_name)
        create_payload_indexes(collection_name, config["indexes"])
        created.append(
            {
                "name": collection_name,
                "description": config["description"],
                "indexes": sorted(config["indexes"]),
            }
        )

    print(
        json.dumps(
            {
                "status": "ok",
                "qdrant_url": QDRANT_URL,
                "vector_size": VECTOR_SIZE,
                "collections": created,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
