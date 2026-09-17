# Docker Run Guide - MistakeTutor Backend

This guide runs the backend API, Qdrant, and optional DB viewer using Docker Compose.

## Files

```text
backend/docker/Dockerfile
backend/docker/docker-compose.yml
backend/.env
backend/storage/
```

`backend/.env` is the single env file. Docker Compose reads it directly.

## 1. Prepare `.env`

From `backend/`:

```powershell
cd D:\Sourcecode\vinai\lab\hackathon\K4-3A-E402-CAMOI3ANHEM\backend
copy .env.example .env
```

Edit:

```env
AUTH_SECRET_KEY=change-me-in-local-env
```

Use any local secret, for example:

```env
AUTH_SECRET_KEY=local-dev-123456
```

For local non-Docker runs, keep:

```env
QDRANT_URL=http://127.0.0.1:6663
```

For Docker runs, `docker-compose.yml` overrides this inside containers:

```env
QDRANT_URL=http://qdrant:6333
```

## 2. Build and Start

From `backend/docker/`:

```powershell
cd D:\Sourcecode\vinai\lab\hackathon\K4-3A-E402-CAMOI3ANHEM\backend\docker
docker compose up --build -d backend qdrant
```

Check containers:

```powershell
docker compose ps
```

## 3. Open Services

Backend API:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/v1/health
```

Qdrant dashboard:

```text
http://127.0.0.1:6663/dashboard
```

Qdrant health:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/healthz
```

## 4. Init Qdrant Collections

Run after backend and Qdrant are up:

```powershell
docker compose exec backend python scripts/init_qdrant_collection.py
```

Expected collections:

```text
mistaketutor_sources
mistaketutor_explanations
mistaketutor_gap_diagnoses
mistaketutor_eval_cases
```

List collections from host:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/collections
```

## 5. Optional DB Viewer

Start the DB viewer:

```powershell
docker compose --profile tools up -d db-ui
```

Open:

```text
http://127.0.0.1:8001
```

Stop DB viewer only:

```powershell
docker compose stop db-ui
```

## 6. Logs

Backend logs:

```powershell
docker compose logs -f backend
```

Qdrant logs:

```powershell
docker compose logs -f qdrant
```

## 7. Rebuild After Code Changes

If Python code or scripts changed:

```powershell
docker compose up --build -d backend
```

Run backend tests inside Docker:

```powershell
docker compose exec backend pytest
```

Then rerun Qdrant init if collection schema changed:

```powershell
docker compose exec backend python scripts/init_qdrant_collection.py
```

Quick-test curriculum APIs:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules
```

Pretty JSON:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules) | ConvertTo-Json -Depth 10
```

Then use the returned `id`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules/1/concepts
```

Pretty JSON:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules/1/concepts) | ConvertTo-Json -Depth 10
```

Run only curriculum tests inside Docker:

```powershell
docker compose exec backend pytest tests/test_curriculum.py
```

Run the full backend workflow test:

```powershell
docker compose exec backend pytest tests/test_workflow.py
```

## 8. Stop

Stop containers:

```powershell
docker compose down
```

Stop and remove local Docker volumes created by Compose:

```powershell
docker compose down -v
```

This project stores SQLite/Qdrant data in:

```text
backend/storage/
```

That folder is gitignored.

## Troubleshooting

### `Connection refused` when init Qdrant from backend container

Cause: the container is using host URL `127.0.0.1:6663`.

Fix: make sure `docker/docker-compose.yml` has this override for `backend`:

```yaml
environment:
  QDRANT_URL: http://qdrant:6333
```

Then rebuild:

```powershell
docker compose up --build -d backend qdrant
```

### Qdrant UI

Open:

```text
http://127.0.0.1:6663/dashboard
```
