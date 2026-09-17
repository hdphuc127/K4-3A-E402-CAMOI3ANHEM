# Vấn đề đã biết

Cập nhật: 17/9. Sắp theo mức độ chặn.

---

## 1. 🔴 CHẶN — Frontend không build được ở bản clone sạch

**Hiện tượng.** Clone repo về, chạy `npm install && npm run dev` trong `frontend/` sẽ fail vì 6 module không tồn tại.

**Nguyên nhân.** `.gitignore` ở thư mục gốc là template Python của GitHub. Dòng 17 là `lib/` — không có dấu `/` đứng trước nên nó khớp thư mục `lib` ở **mọi độ sâu**, và đã nuốt trọn `frontend/src/lib/`. Thư mục này không có trên disk lẫn trong bất kỳ commit nào.

```bash
$ git check-ignore -v frontend/src/lib/utils.ts
.gitignore:17:lib/    frontend/src/lib/utils.ts
```

Các module bị thiếu:

| Import | Nơi dùng |
| --- | --- |
| `@/lib/utils` | cả 46 component trong `frontend/src/components/ui/` |
| `@/lib/review-data` | `frontend/src/routes/index.tsx` |
| `@/lib/tutor-replies` | `frontend/src/routes/index.tsx`, `TutorChat.tsx` |
| `./lib/error-capture`, `./lib/error-page` | `frontend/src/server.ts`, `start.ts` |
| `../lib/lovable-error-reporting` | `frontend/src/routes/__root.tsx` |

**Ảnh hưởng.** Không quay được video demo CP3/CP5 từ một bản clone. Người mới vào nhóm không chạy được ứng dụng.

**Cách sửa (1 dòng).** Đổi `.gitignore` dòng 17 từ `lib/` thành `/lib/`. Ý định gốc của template Python là "thư mục build ở gốc repo", nên neo `/` vừa đúng ngữ nghĩa vừa gỡ được frontend. Sau đó:

```bash
git add -f frontend/src/lib
```

**Lưu ý trước khi sửa.** `.gitignore` là file dùng chung và nhánh này có Lovable đồng bộ (xem `frontend/AGENTS.md`: không force-push, không rebase). Nên commit riêng một commit và **báo Trâm Anh trước**.

**Trạng thái:** chưa sửa — chờ quyết định của chủ sở hữu `frontend/`.

---

## 2. 🟠 `.gitignore` thiếu hai mục mà quy tắc cuộc thi bắt buộc

`THỰC THI & QUY TẮC VIBECODING` mục 4.1 xếp hạng "quan trọng sinh tử": phải ignore `.env`, `data/`, `*.pyc`, `node_modules/`, `.venv/`.

Hiện `.gitignore` gốc **có** `.env`, `.venv`, `*.pyc`, nhưng **thiếu `data/` và `node_modules/`**.

- `node_modules/` được `frontend/.gitignore` lo → rủi ro thấp.
- **`data/` hoàn toàn không được ignore** → chỉ cần một lần `git add .` là dữ liệu thật `vlearn-pack/` bị đẩy lên GitHub public. Đây là rủi ro loại vi phạm nghiêm trọng nhất trong quy chế.

**Cách sửa.** Thêm vào cuối `.gitignore`:

```gitignore
# --- Quy tac cuoc thi: KHONG BAO GIO commit du lieu that ---
data/
vlearn-pack/
discord-pack/
node_modules/
```

Thao tác này thuần cộng thêm, không bỏ ignore của ai. **Trạng thái:** chưa sửa — cần Leader duyệt vì đụng file dùng chung.

---

## 3. 🟡 Tài liệu ghi Next.js, code thực tế là stack khác

`TECH_STACK.md`, `RULES.md`, `Modules.md` và `AGENT.md` đều quy định "Next.js 14 App Router". `frontend/package.json` thực tế là một ứng dụng **TanStack Start + Vite + React 19**, không có package `next` nào. `frontend/src/routes/README.md` thậm chí cấm tạo `app/layout.tsx`.

**Quyết định của Leader:** để nguyên, không sửa cả tài liệu lẫn code trong giai đoạn này.

**Rủi ro cần biết trước khi lên sân khấu.** Nếu giám khảo hỏi kiến trúc frontend ở CP6, trả lời thẳng: giao diện được khởi tạo bằng Lovable nên ra stack TanStack Start; tài liệu stack chưa cập nhật theo. Trả lời trung thực tốt hơn là đọc theo tài liệu rồi bị bắt lỗi.

Để tránh mâu thuẫn lan thêm, `spec.md`, `README.md` và `ARCHITECTURE.md` mới viết đều **mô tả frontend ở mức trung lập** ("SPA React + Tailwind + Shadcn") thay vì gọi tên framework.

---

## 4. 🟡 Mâu thuẫn số liệu và phân công giữa các tài liệu

| Điểm | Bản A | Bản B | Đã chốt |
| --- | --- | --- | --- |
| Kích thước Golden Test Set | 20 câu (`spec.md`, `Modules.md`) | 25 câu (`ARCHITECTUREs.md`, `DECISIONS.md` ADR-003, `Task.md`) | **20 câu** |
| Vai trò Trâm Anh / Hòa | `THỰC THI` mục 4.5: Trâm Anh = AI/RAG, Hòa = Fullstack | `Modules.md`: Trâm Anh = UI/UX, Hòa = AI/RAG | **Theo `Modules.md`** |
| Tên file kiến trúc | `ARCHITECTUREs.md` (thừa chữ "s", nằm trong `main_template/`) | `ARCHITECTURE.md` ở root | **`ARCHITECTURE.md` ở root** — đã tạo |

Các quyết định trên cần được ghi vào `DECISIONS.md` dưới dạng ADR, và ADR-003 cần sửa con số 25 → 20.

---

## 5. 🟡 Bộ quy tắc chưa được commit vào git

`Coding Convention & Vibecoding Rules/` và `Modules.md` hiện đang untracked. Ai clone repo về đều **không có bộ luật của cuộc thi**, kể cả AI editor đang hỗ trợ họ.

**Cách sửa:** `git add "Coding Convention & Vibecoding Rules/" Modules.md`

---

## 6. 🟢 Khoảng cách giữa DoD và giao diện

Hai mục trong DoD hiện chưa demo được vì UI chưa có chỗ hiển thị:

| DoD | Backend | Frontend |
| --- | --- | --- |
| "Mọi câu trả lời kèm dẫn nguồn" | ✅ trả `citations` đúng định dạng | ❌ chưa có component nào render |
| Teach-back diagnosis | ✅ prompt + guardrail đầy đủ | ❌ chưa có ô nhập lời giải thích tự do |

Backend đã ship sẵn hợp đồng để Trâm Anh build song song **mà không cần server chạy**:

- [tests/fixtures/prompts_sample_envelope.json](../tests/fixtures/prompts_sample_envelope.json) — 3 envelope mẫu (thành công / hạ cấp / lỗi)
- [tests/fixtures/prompts_teachback_sample.json](../tests/fixtures/prompts_teachback_sample.json) — một `TeachBackDiagnosis` đầy đủ
- [tests/fixtures/prompts_quiz_ui_shape.json](../tests/fixtures/prompts_quiz_ui_shape.json) — shape quiz chính xác

---

## 7. 🟢 Yêu cầu Python 3.11+

`src/core/prompts/` dùng `StrEnum` và `datetime.UTC`, cả hai chỉ có từ Python 3.11. Máy nào còn Python 3.10 sẽ fail ngay lúc import với lỗi khó đoán.

Kiểm tra: `python --version`. Trên Windows có thể chọn bản cụ thể bằng `py -3.13 -m venv .venv`.
