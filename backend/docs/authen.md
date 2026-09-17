# Authentication & Database API

Tai lieu nay mo ta co che database va cac API authentication hien tai cua backend MistakeTutor.

## 1. Muc tieu

Auth API dung de:

- Tao tai khoan hoc vien dung thu prototype.
- Dang nhap va lay bearer token.
- Lay thong tin user hien tai qua `/auth/me`.
- Tao nen tang de cac API hoc tap sau nay gan ket qua voi tung user.

Backend hien dung SQLite local de chay nhanh trong hackathon. Database duoc tao tu dong khi FastAPI startup.

## 2. Database

### Cau hinh

Trong `backend/.env`:

```env
DATABASE_URL=sqlite:///./storage/mistaketutor.db
AUTH_SECRET_KEY=change-me-in-local-env
AUTH_TOKEN_EXPIRE_MINUTES=1440
```

Luu y:

- `storage/` va cac file `*.db`, `*.sqlite`, `*.sqlite3` da duoc ignore, khong commit len GitHub.
- `AUTH_SECRET_KEY` phai doi trong local `.env`, khong de secret that trong `.env.example`.

### Bang `users`

Backend tu tao bang:

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Y nghia:

| Cot | Kieu | Ghi chu |
|---|---|---|
| `id` | INTEGER | Primary key |
| `email` | TEXT | Unique, dung de login |
| `full_name` | TEXT | Ten hien thi |
| `password_hash` | TEXT | Hash PBKDF2, khong luu password goc |
| `created_at` | TEXT | Thoi diem tao user |

## 3. Co che bao mat hien tai

### Password hashing

File lien quan:

```text
app/core/security.py
```

Co che:

- Password goc khong duoc luu vao database.
- Backend tao salt random bang `secrets.token_hex`.
- Hash bang `hashlib.pbkdf2_hmac("sha256", ..., 120000)`.
- Gia tri luu DB co dang:

```text
pbkdf2_sha256$<salt>$<digest>
```

### Access token

Access token hien tai la token HMAC tu Python standard library, khong phai JWT package.

Payload gom:

```json
{
  "sub": "user_id",
  "email": "learner@example.com",
  "exp": 1790000000
}
```

Token duoc ky bang:

```text
AUTH_SECRET_KEY + HMAC-SHA256
```

Khi goi API can auth, frontend gui:

```text
Authorization: Bearer <access_token>
```

## 4. Response envelope chuan

Tat ca response thanh cong theo dang:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T05:00:00Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

Neu FastAPI raise `HTTPException`, response loi hien tai se theo format mac dinh cua FastAPI:

```json
{
  "detail": "Invalid email or password"
}
```

Sau nay co the bo sung global exception handler de loi cung di theo envelope `success/error/meta`.

## 5. API: Register

```text
POST /api/v1/auth/register
```

Dung de tao user moi va tra ve token dang nhap ngay.

### Request body

```json
{
  "email": "learner@example.com",
  "full_name": "AI20k Learner",
  "password": "password123"
}
```

Validation:

| Field | Rule |
|---|---|
| `email` | Dung format email |
| `full_name` | 1-120 ky tu |
| `password` | 8-128 ky tu |

### Success response

```json
{
  "success": true,
  "data": {
    "access_token": "<token>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "learner@example.com",
      "full_name": "AI20k Learner",
      "created_at": "2026-09-17 12:00:00"
    }
  },
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T05:00:00Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

### Loi co the gap

| Status | Ly do |
|---:|---|
| 409 | Email da ton tai |
| 422 | Body sai schema |

## 6. API: Login

```text
POST /api/v1/auth/login
```

Dung de dang nhap bang email/password va lay access token.

### Request body

```json
{
  "email": "learner@example.com",
  "password": "password123"
}
```

### Success response

Tuong tu register:

```json
{
  "success": true,
  "data": {
    "access_token": "<token>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "learner@example.com",
      "full_name": "AI20k Learner",
      "created_at": "2026-09-17 12:00:00"
    }
  },
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T05:00:00Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

### Loi co the gap

| Status | Ly do |
|---:|---|
| 401 | Sai email hoac password |
| 422 | Body sai schema |

## 7. API: Me

```text
GET /api/v1/auth/me
```

Dung de lay thong tin user hien tai tu access token.

### Header

```text
Authorization: Bearer <access_token>
```

### Success response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "learner@example.com",
    "full_name": "AI20k Learner",
    "created_at": "2026-09-17 12:00:00"
  },
  "error": null,
  "meta": {
    "timestamp": "2026-09-17T05:00:00Z",
    "request_id": null,
    "latency_ms": null
  }
}
```

### Loi co the gap

| Status | Ly do |
|---:|---|
| 401 | Thieu bearer token |
| 401 | Token sai, het han, hoac user khong ton tai |

## 8. Test nhanh bang PowerShell

### Register

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body '{"email":"learner@example.com","full_name":"AI20k Learner","password":"password123"}'
```

### Login

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"learner@example.com","password":"password123"}'

$token = $login.data.access_token
```

### Me

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/api/v1/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }
```

## 9. Cac API tiep theo can lam

Danh sach nay uu tien theo muc tieu CP3-CP4: co AI call that, co log, co metric va demo duoc flow hoc tu loi.

### Nhom A - Learning flow API

| API | Method | Muc dich | Uu tien |
|---|---|---|---|
| `/api/v1/lessons` | GET | List bai hoc/fixture co san, vi du Tokenization | Cao |
| `/api/v1/questions` | GET | Lay cau hoi theo lesson | Cao |
| `/api/v1/attempts` | POST | Luu lan hoc vien tra loi cau hoi | Cao |
| `/api/v1/attempts/{attempt_id}` | GET | Lay lai attempt va ket qua | Trung binh |

### Nhom B - Mistake diagnosis API

| API | Method | Muc dich | Uu tien |
|---|---|---|---|
| `/api/v1/diagnosis` | POST | Da co scaffold: chan doan loi va tra goi y | Da co |
| `/api/v1/diagnosis/{id}/feedback` | POST | User danh dau goi y dung/sai, dung cho validation | Cao |
| `/api/v1/diagnosis/logs` | GET | Xem log cac lan chan doan de quay CP3/CP4 | Trung binh |

### Nhom C - AI/RAG API

| API | Method | Muc dich | Uu tien |
|---|---|---|---|
| `/api/v1/sources/search` | POST | Search transcript/slide lien quan | Cao |
| `/api/v1/sources/{source_id}` | GET | Lay trich dan nguon ngan de hien tren UI | Trung binh |
| `/api/v1/admin/index-sources` | POST | Tao index RAG local tu fixture cho demo | Trung binh |

### Nhom D - Metrics/Evaluation API

| API | Method | Muc dich | Uu tien |
|---|---|---|---|
| `/api/v1/eval/run` | POST | Chay golden set va tinh so dat/sai | Cao cho CP3 |
| `/api/v1/eval/results` | GET | Lay ket qua eval moi nhat | Trung binh |
| `/api/v1/eval/cases` | GET | Xem danh sach golden cases | Trung binh |

### Nhom E - Product ops API

| API | Method | Muc dich | Uu tien |
|---|---|---|---|
| `/api/v1/health` | GET | Da co: kiem tra backend song | Da co |
| `/api/v1/auth/register` | POST | Da co: dang ky | Da co |
| `/api/v1/auth/login` | POST | Da co: dang nhap | Da co |
| `/api/v1/auth/me` | GET | Da co: lay user hien tai | Da co |

## 10. Uu tien lam ngay tiep theo

Nen lam theo thu tu:

1. `POST /api/v1/attempts`: luu cau tra loi cua hoc vien.
2. Nang cap `POST /api/v1/diagnosis`: goi LLM that thay vi rule-based stub.
3. `POST /api/v1/diagnosis/{id}/feedback`: luu user feedback cho validation.
4. `POST /api/v1/eval/run`: chay golden set 20 cases lay so do CP3.

Bo API toi thieu de demo CP3:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/attempts
POST /api/v1/diagnosis
POST /api/v1/eval/run
```
