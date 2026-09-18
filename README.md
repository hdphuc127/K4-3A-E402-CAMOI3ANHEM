# Adaptive VLearn AI Assistant — Ôn tập thông minh

> Trợ giảng AI giúp học viên VLearn **tìm đúng lỗ hổng kiến thức** sau khi học xong một chương, thay vì đọc lại slide một cách mò mẫm.

Mini Hackathon AI · Batch 04 · Ca 3A · Track D (Adaptive Learning) · Nhóm **CÁ MÒI 3 ANH EM**

---

## Sản phẩm giải quyết gì

Khảo sát 5 học viên: **4/5 không xác định được mình đang yếu phần nào** trước khi review, và **3/5 không review lại** sau một chuỗi bài học. Đọc lại slide không phát hiện được chỗ hiểu hời hợt.

Cách tiếp cận của nhóm là **teach-back**: học viên tự giải thích lại khái niệm bằng lời của mình, AI đối chiếu với transcript bài giảng và chỉ ra **đúng một** lỗ hổng quan trọng nhất kèm trích dẫn nguồn, rồi hỏi ngược một câu.

**Nguyên tắc sinh tử của sản phẩm:** AI không bao giờ được kết luận học viên "đã hiểu". Nó chỉ đề xuất điểm cần xem lại, mọi nhận xét đều phải gắn với transcript hoặc rubric. Chi tiết cách cưỡng chế ở ba tầng: [spec.md](spec.md) mục 2.

---

## Phân công

| Thành viên | MSV | Vai trò | Phần việc |
| --- | --- | --- | --- |
| **Hồ Đăng Phúc** | 2A202602796 | Leader & Product Owner | Tài liệu kiến trúc (`spec.md`, `README.md`, `ARCHITECTURE.md`, `docs/`); **System Prompts, Guardrails & Fallback** (`src/core/prompts/`); quản lý 6 checkpoint; slide PDF & pitching |
| **Lê Nguyễn Trâm Anh** | 2A202602760 | UI/UX Developer | Giao diện chat, component trích dẫn, giao diện quiz thích ứng; khảo sát Willing Users; quay video thao tác 30s |
| **Nguyễn Thanh Hòa** | 2A202602559 | AI & RAG Engineer & Tester | RAG Pipeline Hybrid Search (Qdrant + BM25, 70/30); Backend FastAPI `/api/v1/chat`, `/api/v1/quiz`; Golden Test Set & script đo metric |

Ranh giới sở hữu file (để tránh merge conflict): [ARCHITECTURE.md](ARCHITECTURE.md) mục 4.

---

## Trạng thái hiện tại

| Hạng mục | Trạng thái |
| --- | --- |
| System Prompts, Guardrails, Fallback | ✅ Xong — 188 unit test xanh |
| Giao diện web | 🟡 Có, chạy bằng dữ liệu mô phỏng, chưa gọi API |
| RAG Pipeline | ⛔ Chưa bắt đầu |
| Backend API | ⛔ Chưa bắt đầu |
| Golden Test Set & số đo CP3 | ⛔ Chưa bắt đầu |

Khai báo minh bạch đầy đủ: [spec.md](spec.md) mục 5.

---

## Chạy thử

### Backend / tầng AI

Cần **Python 3.11 trở lên** (`StrEnum` và `datetime.UTC` chỉ có từ 3.11).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -e ".[dev]"
```

Chạy toàn bộ test — **không cần API key, không cần vector DB**:

```bash
pytest -q
```

Lint & format:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

Xem một prompt thật được dựng ra như thế nào:

```bash
python -c "from src.core.prompts import build_chat_prompt; import json; \
b = build_chat_prompt('Vì sao LLM có thể bịa?', \
json.load(open('tests/fixtures/prompts_sample_chunks.json', encoding='utf-8'))); \
print(b.system); print('='*60); print(b.user)"
```

Khi có API key, sao chép `.env.example` thành `.env` và điền giá trị. **`.env` không bao giờ được commit.**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

> ⚠️ Ở bản clone sạch, `frontend/src/lib/` bị dòng `lib/` trong `.gitignore` gốc loại khỏi git, nên 6 module bị thiếu và ứng dụng không build được. Xem [docs/known-issues.md](docs/known-issues.md).

---

## Tài liệu

| File | Nội dung |
| --- | --- |
| [spec.md](spec.md) | Deliverable CP4: bài toán, DoD, số đo, khai báo minh bạch |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Cấu trúc thư mục, luồng dữ liệu, ranh giới sở hữu module, response envelope |
| [docs/PROMPT_SPEC.md](docs/PROMPT_SPEC.md) | Thiết kế 4 system prompt, chống prompt injection, bảng 12 guardrail, 18 mã lỗi |
| [docs/data-flow.md](docs/data-flow.md) | Sơ đồ luồng dữ liệu và fallback ladder |
| [docs/pitch-outline.md](docs/pitch-outline.md) | Dàn ý slide 6 trang, kịch bản 7 phút, phân công Q&A |
| [docs/known-issues.md](docs/known-issues.md) | Vấn đề đã biết cần xử lý |
| `Coding Convention & Vibecoding Rules/` | Bộ quy tắc gốc của cuộc thi |

---

## Quy tắc đóng góp

- Nhánh: `feat/<tên>`, `fix/<tên>`. Commit: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`.
- Chạy `pytest -q` và `ruff check src/ tests/` **trước mỗi lần push**.
- Không sửa file ngoài phạm vi sở hữu của mình mà chưa báo chủ sở hữu.
- Không commit `data/`, `vlearn-pack/`, `.env` hay bất kỳ API key nào.
- Không tự cài thêm package khi chưa được Leader duyệt.
- `rag_engine.py` **không được chứa chuỗi prompt** — mọi prompt nằm trong `src/core/prompts/templates/`.
