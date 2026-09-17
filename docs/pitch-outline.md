# Kịch bản Pitching — CP5 & CP6

7 phút trình bày + 3 phút Q&A. Giám khảo chất vấn **ngẫu nhiên từng thành viên**, nên cả ba người đều phải nắm được luồng và kiến trúc.

---

## Thông điệp xuyên suốt

> Sản phẩm không trả lời hộ học viên. Nó tìm ra **đúng một** chỗ học viên đang hiểu sai, và chứng minh bằng chính transcript bài giảng.

Điểm khác biệt để bán: **AI của nhóm bị cấm kết luận học viên "đã hiểu"** — và lệnh cấm đó được cưỡng chế bằng lược đồ dữ liệu chứ không phải bằng lời dặn trong prompt. Đây là câu trả lời mạnh nhất cho câu hỏi kinh điển "làm sao biết AI của bạn không nói quá?".

---

## Slide 6 trang (nộp PDF trước 13:00 · 18/9)

### Trang 1 — Nỗi đau, bằng chứng thật

- Pain một câu: học viên không biết mình đang yếu ở đâu trước khi ôn.
- Số khảo sát 5 học viên: **4/5 không xác định được mình yếu phần nào**; **3/5 không review lại**.
- Nói thẳng giới hạn: mới 1/5 nhớ được trường hợp "tưởng đã hiểu" → nhóm **không** dùng giả thuyết đó làm kết luận chính.

> Nêu giới hạn của bằng chứng ngay từ trang 1 làm tăng độ tin cậy, không giảm. Giám khảo sẽ tìm ra nó nếu mình không nói.

### Trang 2 — Lát cắt một câu & User Flow

- Lát cắt: học viên tự giải thích "vì sao LLM có thể bịa" → AI đối chiếu transcript → chọn **một** lỗ hổng → hỏi ngược.
- Sơ đồ 5 bước (xem [data-flow.md](data-flow.md) mục 3).
- Nhấn: mức automation là **conditional augmentation**, không phải tự động hoàn toàn — và nêu lý do cost-of-error.

### Trang 3 — Kiến trúc AI

- Hybrid Search: Qdrant (dense) 70% + BM25 (sparse) 30%.
- Tầng prompt/guardrail/fallback: 4 system prompt XML, 12 guardrail, 6 tier fallback.
- Sơ đồ rút gọn từ [data-flow.md](data-flow.md) mục 1.

### Trang 4 — Cách chống AI nói bậy (trang mạnh nhất)

Ba cơ chế, mỗi cơ chế một dòng:

1. **Cổng context rỗng** — retrieval không có gì thì hệ thống từ chối *trước khi* gọi LLM. Triệt tiêu nguyên lớp hallucination phổ biến nhất.
2. **Trích dẫn phải đối chiếu được** — mọi `source_id` phải tồn tại thật, mọi `excerpt` phải khớp nguyên văn với tài liệu gốc. Bịa là bị loại tự động.
3. **Enum không có giá trị "UNDERSTOOD"** — model *không thể* kết luận học viên đã hiểu. Cấm bằng lược đồ mạnh hơn cấm bằng văn xuôi.

Kèm một ảnh chụp đoạn `<absolute_rules>` hoặc `<automation_policy>` thật.

### Trang 5 — Số đo

- Bảng Golden Test Set 20 câu: đúng / sai / accuracy **(số thật từ `eval_metrics.py`)**.
- 188 unit test xanh, chạy ~4 giây, không cần API key.
- **Không làm tròn, không tô hồng.** Quy chế ghi rõ "số xấu vẫn đủ điểm nếu là số thật".

### Trang 6 — Khai báo minh bạch & bước tiếp theo

- Bảng 8 hạng mục chưa hoàn thiện, lấy từ [spec.md](../spec.md) mục 5.
- Nói rõ cái gì đã kiểm chứng được và cái gì chưa.

> Khai báo minh bạch **không bị trừ điểm**. Che giấu rồi bị hỏi trúng thì mất nhiều hơn.

---

## Kịch bản 7 phút

| Phút | Nội dung | Người nói |
| --- | --- | --- |
| 0:00–1:00 | Pain + bằng chứng khảo sát + giới hạn bằng chứng | Phúc |
| 1:00–2:00 | Lát cắt một câu + user flow | Phúc |
| 2:00–3:30 | **Demo trực tiếp** (có video backup) | Trâm Anh |
| 3:30–5:00 | Kiến trúc AI + ba cơ chế chống nói bậy | Hòa |
| 5:00–6:00 | Số đo thật trên Golden Test Set | Hòa |
| 6:00–7:00 | Khai báo minh bạch + bước tiếp theo | Phúc |

**Video demo backup bắt buộc quay trước** — phòng hỏng mạng khi pitch.

---

## Phân công Q&A

Mỗi người phải trả lời được **toàn bộ** câu hỏi trong cột của mình mà không cần nhìn tài liệu.

### Phúc — sản phẩm & quyết định

| Câu hỏi có thể gặp | Ý chính khi trả lời |
| --- | --- |
| "Sao chỉ có 5 người khảo sát?" | Thừa nhận mẫu nhỏ. Nêu rõ kết luận nào đủ cơ sở (4/5 không biết mình yếu ở đâu) và kết luận nào chưa (ảo tưởng đã hiểu, mới 1/5). |
| "Vì sao chọn teach-back thay vì chỉ làm quiz?" | Quiz nhận biết đo trí nhớ. Teach-back buộc học viên tự phát biểu cơ chế, lộ ra chỗ hiểu hời hợt mà trắc nghiệm không thấy. |
| "Vì sao AI không tự kết luận học viên đã hiểu?" | Cost-of-error: chẩn đoán sai khiến học viên mang cách hiểu sai sang chương sau. Nên AI chỉ đề xuất, học viên và bài kiểm tra quyết định. |
| "Phần nào chưa xong?" | Đọc thẳng bảng 8 dòng ở `spec.md` mục 5. Không vòng vo. |

### Hòa — AI & kỹ thuật

| Câu hỏi có thể gặp | Ý chính khi trả lời |
| --- | --- |
| "Làm sao chặn hallucination?" | Ba lớp: cổng context rỗng trước khi gọi LLM; `<grounding_policy>` trong prompt; guardrail đối chiếu `source_id` và `excerpt` sau khi trả lời. |
| "Làm sao biết trích dẫn không bịa?" | `source_id` phải nằm trong tập chunk đã đưa vào prompt; `excerpt` phải khớp nguyên văn (độ chứa token ≥ 0.85). Không khớp là bị loại, có unit test. |
| "Tỷ số 70/30 lấy đâu ra?" | Nói thật: chọn theo ADR-001, chưa tinh chỉnh bằng thực nghiệm trên dữ liệu của nhóm. |
| "LLM chết thì sao?" | Thang 6 tier, deadline 10 giây. Tier T3 ghép câu trả lời từ chính đoạn tài liệu đã truy xuất — vẫn có trích dẫn, không sập. |
| "Sao không dùng thư viện guardrail có sẵn?" | Guardrail của nhóm là code thuần, 0 dependency mới, chạy dưới 1 ms và test được không cần API key. Quan trọng hơn: nó kiểm đúng thứ đặc thù của bài toán này — trích dẫn có thật và cụm từ bị cấm. |

### Trâm Anh — trải nghiệm & kiểm thử

| Câu hỏi có thể gặp | Ý chính khi trả lời |
| --- | --- |
| "Học viên có thật sự chịu ngồi gõ giải thích không?" | Đây là giả thuyết đang kiểm chứng với Willing Users. Nói thật kết quả thử nghiệm đã có. |
| "Nếu AI chỉ sai lỗ hổng thì sao?" | Học viên luôn mở được nguồn để đối chiếu, và trạng thái "đã ôn" chỉ do bài trắc nghiệm quyết định, không do AI. |
| "Đã ai ngoài nhóm dùng thử chưa?" | Trả lời bằng số thật từ Willing Users. |

---

## Checklist trước giờ pitch

- [ ] Điền tên **2 Willing Users thật** vào `spec.md` mục 1 (đang để trống)
- [ ] Chạy `eval_metrics.py`, điền số thật vào `spec.md` mục 4 và slide trang 5
- [ ] Xuất slide ra **PDF** (nộp file, không nộp link)
- [ ] Quay **video demo backup**
- [ ] Sửa `.gitignore` để frontend build được từ bản clone sạch — xem [known-issues.md](known-issues.md) mục 1
- [ ] Cả ba người đọc lại `ARCHITECTURE.md` mục 2 và 4
- [ ] Mỗi người tự trả lời to từng câu trong bảng Q&A của mình một lượt
