from fastapi.testclient import TestClient

from app.db.session import initialize_database
from app.main import app


client = TestClient(app)


def test_list_modules_returns_seeded_llm_review_module() -> None:
    initialize_database()

    response = client.get("/api/v1/modules")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"][0]["slug"] == "llm-review"
    assert body["data"][0]["track"] == "D"


def test_list_concepts_by_module_returns_hallucination_concept() -> None:
    initialize_database()
    modules_response = client.get("/api/v1/modules")
    module_id = modules_response.json()["data"][0]["id"]

    response = client.get(f"/api/v1/modules/{module_id}/concepts")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["module"]["id"] == module_id
    assert body["data"]["concepts"][0]["slug"] == "why-llm-hallucinates"


def test_list_concepts_by_unknown_module_returns_404() -> None:
    response = client.get("/api/v1/modules/999999/concepts")

    assert response.status_code == 404
