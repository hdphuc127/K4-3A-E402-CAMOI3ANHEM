# API Reference - MistakeTutor Backend

Base URL local:

```text
http://127.0.0.1:8000/api/v1
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8000/docs
```

## Response Envelope

Successful API responses follow this shape:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T07:42:40.759146Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

## Curriculum & Concepts

These APIs provide learning modules and their key concepts before the learner starts a teach-back session.

### `GET /api/v1/modules`

List all learning modules from table `learning_modules`.

#### Request

```http
GET /api/v1/modules
```

No auth required at the current prototype stage.

#### Example

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules
```

Pretty JSON:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules) | ConvertTo-Json -Depth 10
```

#### Success Response

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "slug": "llm-review",
      "title": "Review chuong LLM",
      "description": "Phien teach-back giup hoc vien phat hien lo hong kien thuc sau khi hoc chuong LLM.",
      "track": "D",
      "created_at": "2026-09-17 06:13:04"
    }
  ],
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T07:42:40.759146Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

#### Data Fields

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Module id used by downstream APIs |
| `slug` | string | Stable module key |
| `title` | string | Human-readable title |
| `description` | string/null | Short module description |
| `track` | string | Hackathon track, currently `D` |
| `created_at` | string | SQLite timestamp |

### `GET /api/v1/modules/{module_id}/concepts`

List key concepts under a learning module from table `concepts`.

#### Request

```http
GET /api/v1/modules/{module_id}/concepts
```

Path params:

| Param | Type | Meaning |
|---|---|---|
| `module_id` | integer | `learning_modules.id` |

#### Example

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules/1/concepts
```

Pretty JSON:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules/1/concepts) | ConvertTo-Json -Depth 10
```

Get only concepts:

```powershell
$res = Invoke-RestMethod http://127.0.0.1:8000/api/v1/modules/1/concepts
$res.data.concepts | ConvertTo-Json -Depth 10
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "module": {
      "id": 1,
      "slug": "llm-review",
      "title": "Review chuong LLM",
      "description": "Phien teach-back giup hoc vien phat hien lo hong kien thuc sau khi hoc chuong LLM.",
      "track": "D",
      "created_at": "2026-09-17 06:13:04"
    },
    "concepts": [
      {
        "id": 1,
        "module_id": 1,
        "slug": "why-llm-hallucinates",
        "title": "Vi sao LLM co the bia",
        "expected_summary": "Hoc vien can giai thich duoc LLM du doan token dua tren mau da hoc, nen co the tao cau nghe hop ly nhung sai neu thieu nguon can cu hoac truy hoi sai ngu canh.",
        "common_gap": "Chi noi 'AI chua du thong minh' ma khong neu co che du doan token va gioi han nguon can cu.",
        "created_at": "2026-09-17 06:13:04"
      }
    ]
  },
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T07:42:46.203613Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

#### Error Response

If module does not exist:

```json
{
  "detail": "Learning module not found"
}
```

Status:

```text
404 Not Found
```

#### Data Fields

| Field | Type | Meaning |
|---|---|---|
| `module` | object | Parent module |
| `concepts` | array | Concepts under the module |
| `concepts[].id` | integer | Concept id used by teach-back APIs |
| `concepts[].slug` | string | Stable concept key |
| `concepts[].title` | string | Human-readable concept title |
| `concepts[].expected_summary` | string | Rubric/target explanation summary |
| `concepts[].common_gap` | string/null | Common misconception/gap |

## Current Seed Data

Backend startup seeds:

```text
Module:
  id: 1
  slug: llm-review
  title: Review chuong LLM

Concept:
  slug: why-llm-hallucinates
  title: Vi sao LLM co the bia
```

## Diagnosis Scaffold

This endpoint is the current placeholder diagnosis API. It is already wired through the backend pipeline shape:

```text
request -> retrieval context -> prompt name -> diagnosis result -> citation
```

Current behavior is deterministic/rule-based for prototype testing. It still uses the older tokenization sample. The next product API should become:

```text
POST /api/v1/teachback-attempts/{attempt_id}/diagnose
```

### `POST /api/v1/diagnosis`

Diagnose a learner answer and return a hint plus citation.

#### Request

```http
POST /api/v1/diagnosis
Content-Type: application/json
```

Body:

```json
{
  "lesson_id": "t06-tokenization",
  "question_id": "tokenization-basic-01",
  "question_text": "Theo cach tach bang khoang trang, 'I love AI' co may token?",
  "correct_answer": "3",
  "student_answer": "8",
  "student_explanation": null
}
```

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `question_text` | string | Prompt/question shown to learner |
| `correct_answer` | string | Expected answer |
| `student_answer` | string | Learner answer |

Optional/default fields:

| Field | Type | Default |
|---|---|---|
| `lesson_id` | string | `t06-tokenization` |
| `question_id` | string | `tokenization-basic-01` |
| `student_explanation` | string/null | `null` |

#### Example

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/diagnosis" `
  -ContentType "application/json" `
  -Body '{"lesson_id":"t06-tokenization","question_id":"tokenization-basic-01","question_text":"Theo cach tach bang khoang trang, ''I love AI'' co may token?","correct_answer":"3","student_answer":"8"}'
```

Pretty JSON:

```powershell
$body = @{
  lesson_id = "t06-tokenization"
  question_id = "tokenization-basic-01"
  question_text = "Theo cach tach bang khoang trang, 'I love AI' co may token?"
  correct_answer = "3"
  student_answer = "8"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/diagnosis" `
  -ContentType "application/json" `
  -Body $body |
  ConvertTo-Json -Depth 10
```

#### Success Response

```json
{
  "success": true,
  "data": {
    "question_id": "tokenization-basic-01",
    "is_correct": false,
    "misconception": "counting_characters_or_spaces",
    "hint": "Ban co ve dang dem ky tu hoac ca dau cach. Hay tach cau thanh cac cum lien tiep khong co khoang trang roi dem cac cum do.",
    "next_action": "retry_answer",
    "citations": [
      {
        "source_id": "t06-tokenization:tokenization-03",
        "title": "Transcript T06 - Tokenization",
        "excerpt": "Tokenization la buoc chia van ban thanh cac don vi nho hon de mo hinh xu ly. Trong vi du don gian, ta co the tam tach theo khoang trang.",
        "confidence": 0.78
      }
    ],
    "debug_prompt_name": "mistake_diagnosis_v1"
  },
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T07:42:46.203613Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

#### Diagnosis Values

`misconception` can currently be:

```text
answer_is_correct
counting_characters_or_spaces
ambiguous_or_unknown
```

`next_action` can currently be:

```text
retry_answer
ask_for_reasoning
explain_reasoning
```

#### Current Limitation

This endpoint is useful for checking that the backend diagnosis pipeline works, but it is not yet the final Track D teach-back API. For the current product direction, the final diagnosis flow should:

1. Save a teach-back attempt.
2. Retrieve transcript/rubric chunks from SQLite/Qdrant.
3. Diagnose the knowledge gap for `why-llm-hallucinates`.
4. Save the result to `gap_diagnoses`.
5. Return feedback, follow-up question, and citation.
