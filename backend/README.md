# MistakeTutor Backend

FastAPI backend scaffold for the Track D MistakeTutor prototype.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/health
GET http://127.0.0.1:8000/api/v1/health
```

Mistake diagnosis scaffold:

```text
POST http://127.0.0.1:8000/api/v1/diagnosis
```

Example body:

```json
{
  "lesson_id": "t06-tokenization",
  "question_id": "tokenization-basic-01",
  "question_text": "Theo cach tach bang khoang trang, 'I love AI' co may token?",
  "correct_answer": "3",
  "student_answer": "8"
}
```

## Test

```powershell
pytest
```

## Notes

- Do not commit `.env`, API keys, or course data packs.
- AI/RAG logic should live under `app/core/` or a dedicated service module, not inside API route files.
- API responses follow the shared envelope: `success`, `data`, `error`, `meta`.
