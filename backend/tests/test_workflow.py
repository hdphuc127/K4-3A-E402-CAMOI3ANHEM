from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import initialize_database
from app.main import app


client = TestClient(app)


def test_full_backend_workflow() -> None:
    initialize_database()

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    assert health_response.json()["data"]["status"] == "ok"

    email = f"learner-{uuid4().hex[:8]}@example.com"
    password = "password123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Workflow Learner",
            "password": password,
        },
    )
    assert register_response.status_code == 200
    register_body = register_response.json()
    assert register_body["success"] is True
    assert register_body["data"]["user"]["email"] == email
    register_token = register_body["data"]["access_token"]
    assert register_token

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["success"] is True
    access_token = login_body["data"]["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == email

    modules_response = client.get("/api/v1/modules")
    assert modules_response.status_code == 200
    modules_body = modules_response.json()
    assert modules_body["success"] is True
    assert len(modules_body["data"]) >= 1
    module = modules_body["data"][0]
    assert module["slug"] == "llm-review"

    concepts_response = client.get(f"/api/v1/modules/{module['id']}/concepts")
    assert concepts_response.status_code == 200
    concepts_body = concepts_response.json()
    assert concepts_body["success"] is True
    assert concepts_body["data"]["module"]["id"] == module["id"]
    assert len(concepts_body["data"]["concepts"]) >= 1
    concept = concepts_body["data"]["concepts"][0]
    assert concept["slug"] == "why-llm-hallucinates"

    diagnosis_response = client.post(
        "/api/v1/diagnosis",
        json={
            "lesson_id": "t06-tokenization",
            "question_id": "tokenization-basic-01",
            "question_text": "Theo cach tach bang khoang trang, 'I love AI' co may token?",
            "correct_answer": "3",
            "student_answer": "8",
        },
    )
    assert diagnosis_response.status_code == 200
    diagnosis_body = diagnosis_response.json()
    assert diagnosis_body["success"] is True
    assert diagnosis_body["data"]["is_correct"] is False
    assert diagnosis_body["data"]["misconception"] == "counting_characters_or_spaces"
    assert diagnosis_body["data"]["next_action"] == "retry_answer"
    assert diagnosis_body["data"]["citations"][0]["source_id"]
