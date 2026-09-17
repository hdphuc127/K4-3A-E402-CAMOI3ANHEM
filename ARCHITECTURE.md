# ARCHITECTURE — Adaptive VLearn AI Assistant

Tài liệu này định hình cấu trúc mã nguồn, luồng dữ liệu và **ranh giới sở hữu module**. Mục cuối là mục quan trọng nhất trong một repo được vibecode song song bởi ba người.

---

## 1. Cấu trúc thư mục

```
K4-3A-E402-CAMOI3ANHEM/
├── spec.md                      # Deliverable CP4
├── ARCHITECTURE.md              # Tài liệu này
├── README.md                    # Mô tả, phân công, hướng dẫn chạy
├── pyproject.toml               # Deps + ruff + pytest (ĐÃ ĐÓNG BĂNG)
├── .env.example                 # Mẫu biến môi trường, chỉ có tên biến
├── docs/                        # Sơ đồ luồng, thiết kế prompt, kịch bản pitch
├── frontend/                    # Ứng dụng giao diện (SPA, React + Tailwind + Shadcn)
├── src/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Cấu hình hệ thống
│   ├── backend/
│   │   ├── api/                 # Router & endpoints (/api/v1/chat, /api/v1/quiz)
│   │   ├── schemas/             # Pydantic DTO cho request/response
│   │   └── middleware/          # CORS, error handler, logging
│   └── core/
│       ├── rag_engine.py        # Hybrid Search: Qdrant (dense) + BM25 (sparse), 70/30
│       ├── vector_search/       # Kết nối & truy vấn vector store
│       └── prompts/             # System Prompts, Guardrails, Fallback  ← xem mục 4
└── tests/
    ├── conftest.py              # Fixture dùng chung, FakeLlmCaller
    ├── fixtures/                # Dữ liệu mẫu + hợp đồng shape cho UI
    ├── unit/                    # Unit test
    ├── golden_test_set.json     # 20 câu hỏi chuẩn (CP3)
    └── eval_metrics.py          # Script đo Accuracy (CP3)
```

**Quy tắc đặt file (bắt buộc):**

- Giao diện: toàn bộ trong `frontend/`.
- API endpoint: chỉ tạo trong `src/backend/api/`. DTO/Schema đặt tại `src/backend/schemas/`.
- Thuật toán RAG, Prompt, AI Core: tập trung tại `src/core/`. **Tuyệt đối không viết logic truy xuất AI trực tiếp trong file API route hoặc Frontend.**
- Kiểm thử & đo lường: toàn bộ trong `tests/`.
- **Không tự ý thêm file mới vào thư mục gốc.**

---

## 2. Sơ đồ luồng dữ liệu (Data Flow)

```
[ Học viên — Frontend ]
        │ (1) Gửi câu hỏi / lời giải thích
        ▼
[ FastAPI Controller ]
        │ (2) Validate request bằng Pydantic
        ▼
[ Hybrid Retriever — rag_engine.py ]
        ├── Dense Retrieval  (Qdrant)     ── 70%
        └── Sparse Retrieval (BM25)       ── 30%
        │ (3) Top-k chunks
        ▼
┌─────────────────────────────────────────────────────────┐
│  src/core/prompts/                                      │
│                                                         │
│  (4) sanitize_untrusted()   ← escape < > , gắn cờ        │
│  (5) build_*_prompt()       ← dựng XML prompt            │
│  (6) G1–G3 input guardrails ← chặn trước khi gọi LLM     │
│  (7) fallback ladder T0→T5  ← gọi LLM, retry, đổi        │
│                                 provider, hạ cấp         │
│  (8) G4–G12 output guardrails ← lọc trích dẫn, chặn      │
│                                  cụm từ cấm, kiểm cấu    │
│                                  trúc quiz               │
│  (9) success_envelope() / error_envelope()              │
└─────────────────────────────────────────────────────────┘
        │ (10) JSON envelope chuẩn
        ▼
[ Frontend Rendering ]
```

Chi tiết từng bước và sơ đồ fallback ladder: [docs/data-flow.md](docs/data-flow.md).
Thiết kế prompt và bảng guardrail đầy đủ: [docs/PROMPT_SPEC.md](docs/PROMPT_SPEC.md).

---

## 3. Phân tầng dịch vụ

| Tầng | Trách nhiệm |
| --- | --- |
| 1. Presentation | Hiển thị UI/UX, quản lý state client, render Markdown & trích dẫn |
| 2. API & Gateway | Định nghĩa route, validate Pydantic, phân luồng request |
| 3. Business Logic | Chat Service, Assessment Service, quản lý phiên |
| 4. AI Core & RAG | Retrieval, Prompt Templates, gọi LLM, sinh trích dẫn, Guardrail |
| 5. Infrastructure | Vector store, lưu trữ file, tích hợp API ngoài |

### Response Envelope (bắt buộc cho mọi endpoint)

Thành công:

```json
{
  "success": true,
  "data": { "answer": "...", "citations": [
    { "source_id": "vlearn-w2-transcript-lab1#c12",
      "title": "Bài 3 — Vì sao LLM có thể bịa",
      "excerpt": "...", "confidence": 0.89 } ] },
  "error": null,
  "meta": { "timestamp": "2026-09-17T10:54:18Z",
            "request_id": "req-xyz-123", "latency_ms": 450 }
}
```

Lỗi:

```json
{
  "success": false,
  "data": null,
  "error": { "code": "LLM_TIMEOUT", "message": "...", "details": "..." },
  "meta": { "timestamp": "...", "request_id": "...", "latency_ms": 10000 }
}
```

**Bất biến:** `data` luôn có `answer` và `citations`. Luồng quiz **thêm** key `quiz`, luồng teach-back **thêm** key `diagnosis`. Các key trong `meta` chỉ được thêm, không bao giờ bị bỏ đi. Nhờ vậy frontend bind `data.answer` vô điều kiện mà không sợ vỡ khi backend mở rộng.

Envelope mẫu đầy đủ (3 trường hợp: thành công, hạ cấp, lỗi): [tests/fixtures/prompts_sample_envelope.json](tests/fixtures/prompts_sample_envelope.json).

---

## 4. Ranh giới sở hữu module

Repo này được vibecode song song bởi ba người. Bảng dưới đây là thứ ngăn merge conflict. **Không sửa file nằm ngoài cột của mình; nếu cần đổi, báo chủ sở hữu trước.**

| Đường dẫn | Chủ sở hữu | Ghi chú |
| --- | --- | --- |
| `frontend/**` | Trâm Anh | |
| `src/main.py`, `src/config.py`, `src/backend/**` | Hòa | |
| `src/core/rag_engine.py`, `src/core/vector_search/**` | Hòa | |
| `tests/golden_test_set.json`, `tests/eval_metrics.py` | Hòa + Trâm Anh | |
| **`src/core/prompts/**`** | **Phúc** | Hòa `import`, không `edit` |
| `tests/conftest.py`, `tests/unit/test_prompts_*.py`, `tests/fixtures/prompts_*` | Phúc | Tiền tố `prompts_` để không đụng file test của M4 |
| `spec.md`, `README.md`, `ARCHITECTURE.md`, `docs/**` | Phúc | |
| `pyproject.toml`, `.env.example` | Phúc tạo, sau đó **đóng băng** | Cần thêm dependency thì báo Leader |

### Hợp đồng `src/core/prompts` ↔ `rag_engine.py`

Đây là bề mặt tiếp xúc duy nhất giữa hai module:

```python
from src.core.prompts import (
    build_chat_prompt, build_teach_back_prompt, build_quiz_prompt,
    run_guarded_generation,        # guardrail + fallback + envelope, một lệnh
    RetrievedChunk, ErrorCode,
    score_faithfulness,            # cho eval_metrics.py (M4)
)
```

Route chat đầy đủ:

```python
started_at = time.monotonic()
request_id = f"req-{uuid4().hex[:12]}"
chunks = await hybrid_search(req.question, top_k=6)     # code của Hòa
bundle = build_chat_prompt(req.question, chunks, request_id=request_id)
return await run_guarded_generation(
    bundle, call_llm=gemini_client, chunks=chunks,
    request_id=request_id, started_at=started_at,
)
```

Hai tính chất khiến hợp đồng này không va chạm:

1. Mọi hàm nhận `RetrievedChunk | Mapping[str, Any]` và tự validate bên trong → truyền thẳng dict payload từ Qdrant được, **không ai bị ép import type của ai**, hai người build song song được.
2. `LlmCaller` là một `Protocol` → tầng prompt **không import SDK LLM nào**. Hòa inject client thật. Hệ quả: toàn bộ test của tầng prompt chạy trong venv chỉ có `pydantic` + `pytest`.

`run_guarded_generation` **không bao giờ raise** — mọi nhánh lỗi đều kết thúc bằng một envelope hợp lệ, nên route FastAPI không cần khối `try/except` nào.

### Định dạng `source_id` — đã chốt, không đổi

```
{pack}-{week}-{kind}-{lesson}#{chunk_no}
ví dụ: vlearn-w2-transcript-lab1#c12
```

Phải **ổn định qua mọi lần re-index** — tuyệt đối không dùng chỉ số trong list. Guardrail G5 đối chiếu mọi trích dẫn với tập `source_id` thật; nếu id đổi sau mỗi lần index, mọi câu trả lời sẽ bị hạ cấp. Mẫu chuẩn: [tests/fixtures/prompts_sample_chunks.json](tests/fixtures/prompts_sample_chunks.json).

---

## 5. Quy ước bắt buộc

- **Python:** PEP8, `snake_case` cho hàm/biến, `PascalCase` cho class/Pydantic model, `UPPER_SNAKE_CASE` cho hằng số. Lint bằng `ruff check src/ tests/`.
- **TypeScript/React:** `camelCase` cho hàm/biến, `PascalCase` cho component/type, `UPPER_SNAKE_CASE` cho hằng số.
- **Prompt tách khỏi logic:** mọi văn bản prompt và mọi thông điệp hiển thị cho học viên nằm trong `src/core/prompts/templates/`. Test `test_no_long_string_literals_in_logic_modules` quét AST và fail build nếu module logic chứa chuỗi > 120 ký tự.
- **Mọi lời gọi I/O hoặc API AI phải nằm trong `try/except`**, có timeout, và hạ cấp êm thay vì để sập.
- **Không commit** `data/`, `vlearn-pack/`, `.env`, hay bất kỳ API key nào.
- **Không tự cài package** ngoài danh sách trong `pyproject.toml` khi chưa có Leader duyệt.
