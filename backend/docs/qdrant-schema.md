# Qdrant Schema - MistakeTutor

Qdrant stores vectors for the Track D teach-back flow: source retrieval, learner explanations, AI gap diagnoses, and golden eval cases.

## Runtime

| Context | URL |
|---|---|
| From host machine | `http://127.0.0.1:6663` |
| From Docker backend container | `http://qdrant:6333` |
| Dashboard | `http://127.0.0.1:6663/dashboard` |

Important: inside Docker, do **not** use `127.0.0.1:6663`. The backend container must call Qdrant by service name:

```env
QDRANT_URL=http://qdrant:6333
```

`docker/docker-compose.yml` already overrides this value for containers.

## Vector Config

All collections use the same vector config:

```json
{
  "size": 768,
  "distance": "Cosine"
}
```

Keep `EMBEDDING_DIM=768` unless the embedding model changes.

## Collections

The init script creates these collections:

```text
mistaketutor_sources
mistaketutor_explanations
mistaketutor_gap_diagnoses
mistaketutor_eval_cases
```

Run:

```powershell
cd D:\Sourcecode\vinai\lab\hackathon\K4-3A-E402-CAMOI3ANHEM\backend\docker
docker compose up --build -d backend qdrant
docker compose exec backend python scripts/init_qdrant_collection.py
```

## 1. `mistaketutor_sources`

Stores transcript, slide, rubric, and synthetic fixture chunks used for citation and retrieval.

Payload:

```json
{
  "source_id": "llm-hallucination-transcript-01",
  "source_type": "transcript",
  "track": "D",
  "module_slug": "llm-review",
  "concept_slug": "why-llm-hallucinates",
  "title": "Transcript chuong LLM - Hallucination",
  "excerpt": "LLM sinh cau tra loi bang cach du doan token tiep theo...",
  "citation_label": "Transcript LLM / Hallucination / doan 01",
  "chunk_index": 1,
  "lesson_id": "llm-review",
  "rubric_refs": [
    "token_prediction_mechanism",
    "source_grounding_limits",
    "plausible_vs_true"
  ],
  "common_gap": "Chi noi AI chua du thong minh ma khong neu co co che du doan token.",
  "tags": ["llm", "hallucination", "teach-back", "track-d"],
  "created_at": "2026-09-17T00:00:00Z"
}
```

Indexes:

```text
source_id
source_type
module_slug
concept_slug
track
tags
created_at
```

## 2. `mistaketutor_explanations`

Stores learner teach-back answers. Use it later for similarity search between weak explanations.

Payload:

```json
{
  "user_id": 1,
  "session_id": 1,
  "attempt_id": 1,
  "module_slug": "llm-review",
  "concept_slug": "why-llm-hallucinates",
  "attempt_no": 1,
  "prompt": "Hay giai thich vi sao LLM co the bia ma khong nhin tai lieu.",
  "student_explanation": "Vi AI chua du thong minh nen tra loi sai.",
  "created_at": "2026-09-17T00:00:00Z"
}
```

Indexes:

```text
user_id
session_id
attempt_id
module_slug
concept_slug
attempt_no
created_at
```

## 3. `mistaketutor_gap_diagnoses`

Stores AI outputs: detected gap, severity, feedback, and follow-up question.

Payload:

```json
{
  "user_id": 1,
  "session_id": 1,
  "attempt_id": 1,
  "concept_slug": "why-llm-hallucinates",
  "gap_type": "missing_token_prediction_mechanism",
  "severity": "high",
  "feedback": "Ban moi noi AI chua thong minh, nhung chua neu co che du doan token.",
  "followup_question": "LLM sinh cau tra loi tiep theo bang cach nao?",
  "source_id": "llm-hallucination-transcript-01",
  "confidence": 0.82,
  "created_at": "2026-09-17T00:00:00Z"
}
```

Indexes:

```text
user_id
session_id
attempt_id
concept_slug
gap_type
severity
source_id
created_at
```

## 4. `mistaketutor_eval_cases`

Stores golden-set and hard-test cases for CP3/CP4 metrics.

Payload:

```json
{
  "case_id": "eval-llm-hallu-001",
  "case_type": "hard_test",
  "module_slug": "llm-review",
  "concept_slug": "why-llm-hallucinates",
  "input_explanation": "AI bia vi no chua du thong minh.",
  "expected_gap_type": "missing_token_prediction_mechanism",
  "expected_behavior": "Hoi nguoc ve co che du doan token va dan nguon transcript.",
  "difficulty": "medium",
  "split": "cp3",
  "created_at": "2026-09-17T00:00:00Z"
}
```

Indexes:

```text
case_id
case_type
module_slug
concept_slug
expected_gap_type
difficulty
split
created_at
```

## Commands

Health check from host:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/healthz
```

List collections:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/collections
```

Open dashboard:

```text
http://127.0.0.1:6663/dashboard
```
