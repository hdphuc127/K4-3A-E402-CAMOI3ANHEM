# Backend Test Workflow

## Main Workflow Test

The full workflow test is:

```text
tests/test_workflow.py
```

It checks:

1. `GET /api/v1/health`
2. `POST /api/v1/auth/register`
3. `POST /api/v1/auth/login`
4. `GET /api/v1/auth/me`
5. `GET /api/v1/modules`
6. `GET /api/v1/modules/{module_id}/concepts`
7. `POST /api/v1/diagnosis`

The test uses a random email on every run, so it can run repeatedly against the local SQLite database.

## Run Locally

From `backend/`:

```powershell
pytest tests/test_workflow.py
```

Run all tests:

```powershell
pytest
```

## Run In Docker

From `backend/docker/`:

```powershell
docker compose up --build -d backend qdrant
docker compose exec backend pytest tests/test_workflow.py
```

Run all tests in Docker:

```powershell
docker compose exec backend pytest
```

## Notes

If Docker says the test file is missing, rebuild the backend image:

```powershell
docker compose up --build -d backend
```
