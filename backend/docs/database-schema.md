# Database Schema - MistakeTutor Track D

Schema nay bam theo CP1: phat hien lo hong kien thuc sau khi hoc bang flow teach-back.

## Core user/auth

### `users`

Luu tai khoan hoc vien dung prototype.

| Column | Purpose |
|---|---|
| `id` | User id |
| `email` | Login email |
| `full_name` | Ten hien thi |
| `password_hash` | PBKDF2 password hash |
| `created_at` | Thoi diem tao |

## Learning content

### `learning_modules`

Dai dien cho mot chuong/tuan hoc can review.

Seed hien co:

```text
slug = llm-review
title = Review chuong LLM
```

### `concepts`

Khái niệm can hoc vien teach-back.

Seed hien co:

```text
slug = why-llm-hallucinates
title = Vi sao LLM co the bia
```

Cot quan trong:

| Column | Purpose |
|---|---|
| `expected_summary` | Dap an/rubric tom tat de doi chieu |
| `common_gap` | Lo hong pho bien du kien |

### `source_chunks`

Doan nguon ngan tu transcript/slide de AI trich dan khi phan hoi.

| Column | Purpose |
|---|---|
| `source_id` | Ma nguon co the hien tren UI/log |
| `source_type` | `transcript`, `slide`, etc. |
| `excerpt` | Doan trich ngan |
| `citation_label` | Label hien thi |

### `rubric_criteria`

Tieu chi cham cau giai thich cua hoc vien.

Seed hien co cho hallucination:

1. Co che du doan token
2. Gioi han nguon can cu
3. Phan biet nghe hop ly va dung su that

## Learning flow

### `review_sessions`

Mot phien hoc vien review chuong/tuan hoc.

| Column | Purpose |
|---|---|
| `user_id` | Hoc vien |
| `module_id` | Chuong/tuan dang review |
| `status` | `in_progress`, `completed` |
| `started_at` / `completed_at` | Timeline |

### `teachback_attempts`

Moi lan hoc vien tu giai thich lai mot khai niem.

| Column | Purpose |
|---|---|
| `session_id` | Thuoc review session nao |
| `concept_id` | Khai niem dang teach-back |
| `prompt` | Cau hoi giao cho hoc vien |
| `student_explanation` | Cau tra loi/giai thich cua hoc vien |
| `attempt_no` | Lan thu may |

### `gap_diagnoses`

Ket qua AI doi chieu cau giai thich voi transcript/rubric.

| Column | Purpose |
|---|---|
| `attempt_id` | Attempt duoc chan doan |
| `gap_type` | Loai lo hong, vi du `missing_token_prediction_mechanism` |
| `severity` | `low`, `medium`, `high` |
| `feedback` | Nhan xet ngan |
| `followup_question` | Cau hoi nguoc de hoc vien sua cach hieu |
| `confidence` | Muc tu tin |
| `source_chunk_id` | Nguon duoc trich dan |

## Evidence and validation

### `user_research_responses`

Luu log khao sat CP1/R1.

| Column | Purpose |
|---|---|
| `respondent_label` | Ten/ma nguoi tra loi, co the an danh |
| `question` | Cau hoi da hoi |
| `answer` | Cau tra loi nguyen van |
| `normalized_answer` | Nhom cau tra loi de dem |
| `evidence_note` | Ghi chu phan tich |

### `willing_users`

Luu danh sach willing users khai tu CP1 va dung cho validation.

| Column | Purpose |
|---|---|
| `full_name` | Ten user that |
| `class_room` | Lop/phong |
| `commitment_note` | Cam ket thu |
| `planned_test_time` | Thoi gian du kien |
| `status` | `planned`, `tested`, `cancelled` |

## Tables cần API tiếp theo

Nen lam API theo thu tu:

1. `GET /api/v1/modules`
2. `GET /api/v1/modules/{module_id}/concepts`
3. `POST /api/v1/review-sessions`
4. `POST /api/v1/teachback-attempts`
5. `POST /api/v1/teachback-attempts/{attempt_id}/diagnose`
6. `POST /api/v1/research-responses`
7. `POST /api/v1/willing-users`
