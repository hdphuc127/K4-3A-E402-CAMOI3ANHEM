from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_diagnosis_returns_retry_hint_for_character_counting_error() -> None:
    response = client.post(
        "/api/v1/diagnosis",
        json={
            "lesson_id": "t06-tokenization",
            "question_id": "tokenization-basic-01",
            "question_text": "Theo cach tach bang khoang trang, 'I love AI' co may token?",
            "correct_answer": "3",
            "student_answer": "8",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_correct"] is False
    assert body["data"]["misconception"] == "counting_characters_or_spaces"
    assert body["data"]["citations"][0]["source_id"] == "t06-tokenization:tokenization-03"
