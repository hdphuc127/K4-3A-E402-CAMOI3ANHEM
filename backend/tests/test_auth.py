from fastapi.testclient import TestClient

from app.db.session import initialize_database
from app.main import app


client = TestClient(app)


def test_register_login_and_me_flow() -> None:
    initialize_database()
    email = "learner@example.com"
    password = "password123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "AI20k Learner",
            "password": password,
        },
    )

    assert register_response.status_code in {200, 409}

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == email
