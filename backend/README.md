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

Local database viewer:

```text
uvicorn app.db_ui:app --reload --port 8001
http://127.0.0.1:8001
```

This app is for local development only. Do not expose it publicly.

## Qdrant

Start local Qdrant on port `6663`:

```powershell
docker compose -f docker-compose.qdrant.yml up -d
```

Create the MistakeTutor collections and payload indexes:

```powershell
python scripts/init_qdrant_collection.py
```

Qdrant dashboard/API:

```text
http://127.0.0.1:6663
```

Schema notes:

```text
docs/qdrant-schema.md
```

## Docker

Docker files live in:

```text
docker/
```

Run backend + Qdrant:

```powershell
copy .env.example .env
cd docker
docker compose up --build -d
```

More details:

```text
docker/README.md
docs/docker-run.md
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

Auth endpoints:

```text
POST http://127.0.0.1:8000/api/v1/auth/register
POST http://127.0.0.1:8000/api/v1/auth/login
GET  http://127.0.0.1:8000/api/v1/auth/me
```

Register body:

```json
{
  "email": "learner@example.com",
  "full_name": "AI20k Learner",
  "password": "password123"
}
```

Login body:

```json
{
  "email": "learner@example.com",
  "password": "password123"
}
```

Use the `access_token` from register/login as:

```text
Authorization: Bearer <access_token>
```

Curriculum endpoints:

```text
GET http://127.0.0.1:8000/api/v1/modules
GET http://127.0.0.1:8000/api/v1/modules/{module_id}/concepts
```

## Test

```powershell
pytest
```

## Notes

- Do not commit `.env`, API keys, or course data packs.
- AI/RAG logic should live under `app/core/` or a dedicated service module, not inside API route files.
- API responses follow the shared envelope: `success`, `data`, `error`, `meta`.
