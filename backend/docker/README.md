# Docker Runbook

This folder hosts the Docker setup for the MistakeTutor backend.

## 1. Prepare env

```powershell
cd K4-3A-E402-CAMOI3ANHEM\backend
copy .env.example .env
```

Edit `backend\.env` and replace:

```env
AUTH_SECRET_KEY=change-me-in-local-env
```

with a local secret.

## 2. Build and run backend

```powershell
cd K4-3A-E402-CAMOI3ANHEM\backend\docker
docker compose up --build -d
```

Backend:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/v1/health
```

Qdrant:

```text
http://127.0.0.1:6663
```

## 3. Run DB viewer

The DB viewer is optional and uses the `tools` profile.

```powershell
docker compose --profile tools up -d db-ui
```

Open:

```text
http://127.0.0.1:8001
```

## 4. Init Qdrant collection

After Qdrant is running:

```powershell
docker compose exec backend python scripts/init_qdrant_collection.py
```

## 5. Logs

```powershell
docker compose logs -f backend
docker compose logs -f qdrant
```

## 6. Stop

```powershell
docker compose down
```

Keep storage:

```text
backend/storage
```

The storage folder is gitignored and contains SQLite/Qdrant local data.
