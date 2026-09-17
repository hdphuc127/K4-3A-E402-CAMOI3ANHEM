# Frontend API Workflow

Workflow nay kiem tra cac API ma frontend dang goi trong MVP:

- `GET /api/v1/health`
- `GET /api/v1/review-data`
- `GET /api/v1/modules`
- `GET /api/v1/modules/{module_id}/concepts`
- `POST /api/v1/diagnosis`

## Chay backend bang Docker

Tu thu muc `backend/docker`:

```powershell
docker compose up -d qdrant backend
```

Neu can nap lai RAG data:

```powershell
docker compose run --rm -e RAG_FORCE_REINGEST=true rag-ingest
docker compose up -d qdrant backend
```

## Chay workflow test API cua frontend

Tu thu muc `frontend`:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000/api/v1"
powershell -ExecutionPolicy Bypass -File .\tests\api-workflow.ps1
```

Hoac chi ro API base truc tiep:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\api-workflow.ps1 -ApiBaseUrl "http://127.0.0.1:8000/api/v1"
```

Ket qua dung se ket thuc bang:

```text
Workflow passed. Frontend can call the backend APIs used in the MVP flow.
```

## Chay frontend

Tu thu muc `frontend`:

```powershell
npm.cmd run dev
```

Mo:

```text
http://localhost:8080/
```
