# Database Schema - MistakeTutor Track D

SQLite stores relational product state: users, learning modules, review sessions, teach-back attempts, diagnoses, research evidence, and willing users.

DB file:

```text
backend/storage/mistaketutor.db
```

The file is gitignored.

## Startup Behavior

`app/db/session.py` creates all tables automatically on FastAPI startup:

```text
uvicorn app.main:app --reload --port 8000
```

It also seeds the default CP1 content:

```text
Module:  llm-review
Concept: why-llm-hallucinates
Topic:   Vi sao LLM co the bia
```

## 1. Auth

### `users`

Stores learner accounts.

| Column | Purpose |
|---|---|
| `id` | User id |
| `email` | Unique login email |
| `full_name` | Display name |
| `password_hash` | PBKDF2 hash, never raw password |
| `created_at` | Created timestamp |

Related APIs:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

## 2. Learning Content

### `learning_modules`

Represents a chapter/week to review.

Seed:

| Field | Value |
|---|---|
| `slug` | `llm-review` |
| `title` | `Review chuong LLM` |
| `track` | `D` |

### `concepts`

Represents a concept learners must explain back.

Seed:

| Field | Value |
|---|---|
| `slug` | `why-llm-hallucinates` |
| `title` | `Vi sao LLM co the bia` |
| `common_gap` | Learner says only "AI is not smart enough" and misses token prediction/source grounding |

Important columns:

| Column | Purpose |
|---|---|
| `module_id` | Parent module |
| `expected_summary` | Expected answer/rubric summary |
| `common_gap` | Common misconception |

Related APIs:

```text
GET /api/v1/modules
GET /api/v1/modules/{module_id}/concepts
```

### `source_chunks`

Short excerpts from transcript/slide/rubric used as evidence and citations.

| Column | Purpose |
|---|---|
| `concept_id` | Related concept |
| `source_id` | Stable source id |
| `source_type` | `transcript`, `slide`, `rubric`, `synthetic_fixture` |
| `title` | Source title |
| `excerpt` | Short citation excerpt |
| `citation_label` | UI-friendly label |

### `rubric_criteria`

Scoring criteria for a learner's explanation.

Seeded criteria for `why-llm-hallucinates`:

1. `Co che du doan token`
2. `Gioi han nguon can cu`
3. `Phan biet nghe hop ly va dung su that`

## 3. Learning Flow

### `review_sessions`

One learner's review session for a module.

| Column | Purpose |
|---|---|
| `user_id` | Learner |
| `module_id` | Module being reviewed |
| `status` | `in_progress`, `completed` |
| `started_at` | Start timestamp |
| `completed_at` | End timestamp |

### `teachback_attempts`

One learner answer to one teach-back prompt.

| Column | Purpose |
|---|---|
| `session_id` | Parent review session |
| `concept_id` | Concept being explained |
| `prompt` | Prompt shown to learner |
| `student_explanation` | Learner answer |
| `attempt_no` | Attempt number |

### `gap_diagnoses`

AI diagnosis for a teach-back attempt.

| Column | Purpose |
|---|---|
| `attempt_id` | Diagnosed attempt |
| `gap_type` | Gap code, e.g. `missing_token_prediction_mechanism` |
| `severity` | `low`, `medium`, `high` |
| `feedback` | Short feedback |
| `followup_question` | Socratic question to repair understanding |
| `confidence` | AI confidence score |
| `source_chunk_id` | Citation source |

## 4. Evidence and Validation

### `user_research_responses`

Stores CP1/R1 survey and interview evidence.

| Column | Purpose |
|---|---|
| `respondent_label` | Name or anonymized label |
| `question` | Asked question |
| `answer` | Raw answer |
| `normalized_answer` | Bucket for counting |
| `evidence_note` | Analysis note |

### `willing_users`

Stores users who agreed to test the prototype.

| Column | Purpose |
|---|---|
| `full_name` | Real tester name |
| `class_room` | Class/room |
| `commitment_note` | What they agreed to test |
| `planned_test_time` | Planned validation time |
| `status` | `planned`, `tested`, `cancelled` |

## Next APIs to Build

Recommended order:

1. `POST /api/v1/review-sessions`
2. `POST /api/v1/teachback-attempts`
3. `POST /api/v1/teachback-attempts/{attempt_id}/diagnose`
4. `POST /api/v1/research-responses`
5. `POST /api/v1/willing-users`
6. `POST /api/v1/eval/run`

Minimum CP3 demo path:

```text
auth/login
create review session
create teach-back attempt
diagnose gap
show citation + follow-up question
```
