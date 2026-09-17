from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_health_check_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["error"] is None
    assert body["meta"]["timestamp"]


def test_versioned_health_check_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "MistakeTutor API"
