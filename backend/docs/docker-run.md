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

Important:

- Do not copy `.env` into the Docker image.
- Do not commit `.env` to Git.
- `docker-compose.yml` uses `env_file: ../.env`, so secrets are injected only when the container runs.
- `docker/.dockerignore` excludes `.env`, `.env.*`, and `storage/` from the build context.

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
AUTH_SECRET_KEY=replace-with-a-long-random-local-secret
```

For local non-Docker runs, keep:

```env
QDRANT_URL=http://127.0.0.1:6663
```

For Docker runs, `docker-compose.yml` overrides this inside containers:

```env
QDRANT_URL=http://qdrant:6333
```

If you use OpenAI, set these in `backend/.env`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=replace-with-your-openai-key
DEFAULT_LLM_MODEL=gpt-4o-mini
LLM_PRIMARY_PROVIDER=openai
LLM_FALLBACK_PROVIDER=gemini
```

Keep `GEMINI_API_KEY=` empty unless you want Gemini fallback.

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

Verify that the backend container received the env without printing the key:

```powershell
docker compose exec backend python -c "from app.core.config import settings; print({'provider': settings.llm_primary_provider, 'model': settings.default_llm_model, 'has_openai_key': bool(settings.openai_api_key)})"
```

Expected:

```text
{'provider': 'openai', 'model': 'gpt-4o-mini', 'has_openai_key': True}
```

## 2.1. Auto Ingest VLearn RAG Data

Docker Compose also runs `rag-ingest` before starting `backend`.

It mounts the local data pack:

```text
D:\Sourcecode\vinai\lab\hackathon\data\vlearn-pack
```

into the container:

```text
/app/data/vlearn-pack
```

extracts PDF slide text with `pypdf`, then sends extracted text to OpenAI Embeddings before upserting transcript/chatlog/PDF chunks into Qdrant collection:

```text
mistaketutor_sources
```

Default ingest settings:

```env
VLEARN_PACK_PATH=/app/data/vlearn-pack
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
VLEARN_CHATLOG_MAX_ROWS=3000
RAG_CHUNK_CHARS=1400
RAG_CHUNK_OVERLAP=180
```

The ingest is idempotent. If `vlearn-pack` already exists in Qdrant, it skips.

Check ingest logs:

```powershell
docker compose logs --no-color rag-ingest
```

Example first run:

```json
{
  "status": "ok",
  "collection": "mistaketutor_sources",
  "points_upserted": 3484,
  "embedding": "openai",
  "embedding_model": "text-embedding-3-small"
}
```

Expected later runs:

```json
{"status": "skipped", "reason": "vlearn-pack already ingested"}
```

Count VLearn RAG points:

```powershell
Invoke-RestMethod -Method Post `
  -ContentType 'application/json' `
  -Body '{"exact":true,"filter":{"must":[{"key":"source_pack","match":{"value":"vlearn-pack"}}]}}' `
  http://127.0.0.1:6663/collections/mistaketutor_sources/points/count
```

Force reingest:

```powershell
docker compose run --rm -e RAG_FORCE_REINGEST=true rag-ingest
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
