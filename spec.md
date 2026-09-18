# SPEC — Adaptive VLearn AI Assistant

_Deliverable chuẩn CP4 · Mini Hackathon AI Batch 04 · Ca 3A · Nhóm CẢ MỜI 3 ANH EM_

---

## 1. MÔ TẢ TỔNG QUAN & BÀI TOÁN (PROBLEM & SCOPE)

- **Tên dự án / Sản phẩm:** Adaptive VLearn AI Assistant — Ôn tập thông minh
- **Track lựa chọn:** Track D — Học tập thích ứng & Tương tác (Adaptive Learning)
- **Thành viên nhóm:**
  - Hồ Đăng Phúc (2A202602796) — Leader & Product Owner
  - Lê Nguyễn Trâm Anh (2A202602760) — UI / UX Developer
  - Nguyễn Thanh Hòa (2A202602559) — AI & RAG Engineer & Tester

### Khảo sát nỗi đau thực tế (Problem & Pain Points)

**Pain một câu:** Một học viên vừa học xong một chương đang cố kiểm tra xem mình đã hiểu bài chưa, nhưng việc đọc lại slide hoặc làm câu hỏi nhận biết không phát hiện được những chỗ mình đang hiểu hời hợt hoặc hiểu sai, khiến học viên mang lỗ hổng đó sang bài tập và các chương tiếp theo.

**Bằng chứng khảo sát (5 học viên):**

| Câu hỏi khảo sát | Kết quả |
| --- | --- |
| "Trước khi review, bạn có biết rõ mình đang yếu hoặc chưa hiểu phần nào không?" | 3/5 "Hoàn toàn không biết", 1/5 "Khá mơ hồ", 1/5 "Biết rõ" |
| "Cuối tuần hoặc sau một chuỗi bài học, bạn có thường review lại không?" | 3/5 "Không", 2/5 "Thỉnh thoảng", 0/5 "Thường xuyên" |
| "Có phần nào bạn nghĩ đã hiểu, nhưng khi tự giải thích mới thấy chưa chắc?" | 1/5 "Có", 3/5 "Không", 1/5 "Không nhớ" |

**Giới hạn của bằng chứng (khai báo thành thật):** 4/5 học viên chưa xác định rõ mình yếu ở đâu trước khi review — đây là pain chính, có cơ sở. Nhưng mới 1/5 nhớ được trường hợp "tưởng đã hiểu", nên nhóm **không** dùng giả thuyết "ảo tưởng đã hiểu" làm kết luận chính; nó vẫn đang được kiểm chứng thêm.

### Lát cắt MỘT CÂU

> Một học viên vừa học xong chương về LLM · giải thích lại khái niệm "vì sao LLM có thể bịa" mà không nhìn tài liệu · AI đối chiếu lời giải thích với transcript và quyết định **một** lỗ hổng quan trọng nhất để hỏi ngược · học viên bổ sung và giải thích đúng khái niệm theo rubric.

### Tập người dùng mục tiêu & Willing Users (CP1)

- Nguyễn Văn Xuân Lộc
- Nguyễn Thị Thùy Dương

---

## 2. KIẾN TRÚC GIẢI PHÁP & TRẢI NGHIỆM NGƯỜI DÙNG (USER FLOW & AI ARCHITECTURE)

### User Flow

1. Học viên chọn tuần / chương vừa học trên giao diện web.
2. Làm một bài kiểm tra nhanh để hệ thống khoanh vùng chủ đề còn yếu.
3. Với chủ đề yếu, học viên **tự giải thích lại khái niệm bằng lời của mình** (teach-back), không nhìn tài liệu.
4. AI đối chiếu lời giải thích với transcript + rubric, chỉ ra **đúng một** lỗ hổng quan trọng nhất kèm trích dẫn nguồn, và hỏi ngược một câu.
5. Học viên bổ sung, rồi làm bài trắc nghiệm thích ứng để xác nhận. Câu sai được giải thích kèm dẫn nguồn.

### Kiến trúc kỹ thuật AI (Core AI Engine)

- **RAG Pipeline:** Hybrid Search — Dense Vector Search (Qdrant) kết hợp Sparse Search (BM25) theo tỷ lệ 70/30 trên kho dữ liệu VLearn pack (transcript + slide).
- **System Prompts & Guardrails:** Quản lý tập trung tại `src/core/prompts/`, viết bằng cấu trúc XML có `<absolute_rules>`, `<grounding_policy>`, `<citation_policy>`, `<untrusted_content_policy>` và `<final_reminders>`. **Nghiêm cấm bịa đặt kiến thức không có trong tài liệu bài giảng.**
- **Chống prompt injection 2 lớp:** một bộ sanitizer deterministic escape `<` / `>` trước khi văn bản chạm vào prompt (bảo đảm cấu trúc), cộng với `<untrusted_content_policy>` trong prompt (bảo đảm ngữ nghĩa).
- **Fallback Handling:** Thang 6 tier với deadline toàn cục 10 giây; khi LLM timeout / rate-limit, hệ thống trả lời trích xuất trực tiếp từ tài liệu đã truy xuất thay vì báo lỗi, nên vẫn giữ được dẫn nguồn.

### Cam kết sản phẩm quan trọng nhất

> **AI không bao giờ được kết luận rằng học viên "đã hiểu".**

Mức automation của sản phẩm là **conditional augmentation**: AI chỉ *đề xuất* một điểm cần xem lại, mọi nhận xét phải gắn với transcript hoặc rubric, và học viên luôn mở được nguồn để kiểm tra. Lý do theo cost-of-error: nếu AI chẩn đoán sai, học viên sẽ mang cách hiểu sai đó sang chương sau.

Cam kết này được cưỡng chế ở **ba tầng**, không chỉ bằng lời dặn trong prompt:

| Tầng | Cơ chế | Vì sao đủ mạnh |
| --- | --- | --- |
| 1. Lược đồ dữ liệu | Enum `verdict` chỉ có `GAP_FOUND`, `NEEDS_MORE_EVIDENCE`, `OFF_TOPIC` — **không tồn tại giá trị `UNDERSTOOD`** | Structured output ép model chọn trong ba giá trị đó, nên model *không thể phát ngôn* kết luận này. Không phụ thuộc vào việc model có nghe lời hay không. |
| 2. Từ vựng | Guardrail regex chặn ~15 biến thể ("bạn đã hiểu", "đã nắm vững", "không cần ôn lại"…) trên mọi trường văn bản | Bắt cả trường hợp model diễn đạt vòng vo |
| 3. Hệ thống | Chỉ phép **so khớp trắc nghiệm deterministic** mới được lật trạng thái một chủ đề sang "Đã ôn & xác nhận" | Hợp đồng backend không có đường nào cho LLM chạm vào trạng thái đó |

---

## 3. TIÊU CHÍ NGHIỆM THU "ĐẠT" (DEFINITION OF DONE — DoD)

_Tiêu chí này được khóa cố định sau 21:00 ngày 17/9 (CP4)._

### Tính năng bắt buộc (Must-have Features)

1. **RAG Retrieval** — tìm và trích xuất thông tin chính xác từ bộ dữ liệu `vlearn-pack/`.
2. **Citation & Traceability** — mọi câu trả lời của AI đều kèm dẫn nguồn cụ thể (tên bài giảng, trang slide hoặc mốc thời gian transcript). Trích dẫn không đối chiếu được với tài liệu gốc sẽ bị hệ thống tự loại bỏ.
3. **Teach-back Diagnosis** — đối chiếu lời giải thích của học viên với transcript, chỉ ra đúng một lỗ hổng kèm bằng chứng, và hỏi ngược một câu.
4. **Adaptive Quiz Generation** — tự động tạo 3–5 câu trắc nghiệm ôn tập thích ứng kèm giải thích cho câu sai.
5. **UI/UX cơ bản** — giao diện web trực quan, phản hồi nhanh.

### Chuẩn "Đạt" về chất lượng

- Đạt tối thiểu **80% độ chính xác** trên Bộ Golden Test Set **20 câu hỏi** (≥ 16/20 câu trả lời đúng và trích dẫn chuẩn nguồn).
- **Không có câu trả lời nào bịa nguồn:** mọi `source_id` trong trích dẫn phải tồn tại thật trong tập tài liệu đã truy xuất.
- **Không có câu nào kết luận học viên "đã hiểu"** trên toàn bộ test set.

---

## 4. BỘ ĐO LƯỜNG & KẾT QUẢ KIỂM THỬ THỰC TẾ (METRICS & TEST RESULTS — CP3)

- **Bộ dữ liệu kiểm thử:** `tests/golden_test_set.json`, gồm 20 câu hỏi thử nghiệm thực tế.
- **Script đo lường:** `tests/eval_metrics.py`.

### Con số đo lường thực tế

> ⚠️ **CHƯA CHẠY.** Các ô dưới đây để trống có chủ ý và sẽ được điền bằng kết quả chạy thật của `eval_metrics.py`. Nhóm **không** điền số ước lượng — theo quy định CP3, "số xấu vẫn đủ điểm nếu là số thật".

| Chỉ số | Giá trị |
| --- | --- |
| Tổng số câu thử nghiệm | 20 |
| Số câu trả lời đúng & chuẩn nguồn | `___` |
| Số câu sai / lỗi / hallucination | `___` |
| **Tỷ lệ chính xác thực tế** | `___%` |
| Số câu bịa `source_id` (phải bằng 0) | `___` |
| Số câu vi phạm luật "đã hiểu" (phải bằng 0) | `___` |

### Số đo đã có tại thời điểm nộp

Tầng System Prompts / Guardrails / Fallback đã có bộ kiểm thử tự động chạy được độc lập, không cần API key:

| Chỉ số | Giá trị |
| --- | --- |
| Số unit test | **188** |
| Kết quả | **188 passed** |
| Thời gian chạy | ~4 giây |
| Lệnh tái lập | `pytest -q` |

---

## 5. BÁO CÁO MINH BẠCH HẠNG MỤC CHƯA HOÀN THIỆN (TRANSPARENCY)

_Khai báo thành thật các mục chưa hoàn thiện tại thời điểm nộp CP4._

| # | Hạng mục | Trạng thái thực tế |
| --- | --- | --- |
| 1 | **Golden Test Set & số đo CP3** | Chưa có. `tests/golden_test_set.json` và `tests/eval_metrics.py` chưa được xây. Mục 4 ở trên vì vậy để trống. |
| 2 | **RAG Pipeline (Hybrid Search)** | Chưa triển khai. `src/core/rag_engine.py` chưa tồn tại. Tầng prompt/guardrail/fallback đã sẵn sàng và có hợp đồng import rõ ràng để đấu nối. |
| 3 | **Backend API** | Chưa triển khai. `/api/v1/chat` và `/api/v1/quiz` chưa tồn tại. |
| 4 | **Đấu nối Frontend ↔ Backend** | Chưa. Giao diện hiện chạy hoàn toàn bằng dữ liệu mô phỏng cục bộ, không gọi API nào. |
| 5 | **Component hiển thị trích dẫn** | Chưa có trên UI. Backend đã trả `citations` đúng định dạng; UI chưa có chỗ render. Đây là khoảng cách trực tiếp với DoD mục 2. |
| 6 | **Màn hình teach-back** | Chưa có. Backend đã có prompt và guardrail đầy đủ cho luồng này; UI chưa có ô nhập lời giải thích tự do. |
| 7 | **Chỉ số Latency** | Chưa đo. Chưa có lần gọi LLM thật nào. |
| 8 | **Semantic Caching, Discord bot, Whisper** | Nằm ngoài phạm vi CP4, không triển khai. |

**Những gì đã thực sự hoàn thành và kiểm chứng được:**

- Bốn System Prompt cấu trúc XML (chat RAG, teach-back diagnosis, adaptive quiz, faithfulness judge).
- Sanitizer chống prompt injection có bảo đảm cấu trúc, kèm test chống cả false-negative lẫn false-positive.
- 12 guardrail deterministic, trong đó có kiểm tra `source_id` có thật và kiểm tra trích dẫn nguyên văn.
- Fallback ladder 6 tier với deadline toàn cục 10 giây, bảng 18 mã lỗi kèm thông điệp tiếng Việt, response envelope đúng chuẩn `CODING_STANDARDS.md`.
- 188 unit test xanh, chạy được trong repo chưa có backend và chưa có API key.
