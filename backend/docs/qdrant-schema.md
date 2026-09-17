# Qdrant Schema - MistakeTutor

Qdrant is used as the vector store for transcript/slide chunks that support teach-back diagnosis.

## Runtime

Docker service:

```text
mistaketutor-qdrant
```

External HTTP port:

```text
http://127.0.0.1:6663
```

Internal container port:

```text
6333
```

Collection:

```text
mistaketutor_sources
```

Default vector config:

```json
{
  "size": 768,
  "distance": "Cosine"
}
```

The vector size should match the embedding model. Keep `EMBEDDING_DIM=768` unless the embedding provider changes.

## Payload JSON

Each Qdrant point should use this payload shape:

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
  "common_gap": "Chi noi AI chua du thong minh ma khong neu co che du doan token.",
  "tags": [
    "llm",
    "hallucination",
    "teach-back",
    "track-d"
  ],
  "created_at": "2026-09-17T00:00:00Z"
}
```

## Required fields

| Field | Type | Purpose |
|---|---|---|
| `source_id` | string | Stable id for source/chunk |
| `source_type` | string | `transcript`, `slide`, `rubric`, or `synthetic_fixture` |
| `track` | string | Hackathon track, here `D` |
| `module_slug` | string | Learning module, e.g. `llm-review` |
| `concept_slug` | string | Concept, e.g. `why-llm-hallucinates` |
| `title` | string | Human-readable source title |
| `excerpt` | string | Short source excerpt shown to learners |
| `citation_label` | string | Citation label rendered in UI |
| `chunk_index` | integer | Order inside a source |
| `tags` | string[] | Filter/search tags |
| `created_at` | datetime string | Point creation time |

## Optional fields

| Field | Type | Purpose |
|---|---|---|
| `lesson_id` | string | Alias for UI lesson selection |
| `rubric_refs` | string[] | Rubric criteria supported by the chunk |
| `common_gap` | string | Misconception this chunk helps diagnose |
| `page` | integer | Slide/page number if available |
| `timestamp_start` | number | Transcript start time if available |
| `timestamp_end` | number | Transcript end time if available |

## Payload indexes

The init script creates indexes for:

```text
source_id
source_type
module_slug
concept_slug
track
tags
created_at
```

## Commands

Start Qdrant:

```powershell
docker compose -f docker-compose.qdrant.yml up -d
```

Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/healthz
```

Create collection and indexes:

```powershell
python scripts/init_qdrant_collection.py
```

List collections:

```powershell
Invoke-RestMethod http://127.0.0.1:6663/collections
```
