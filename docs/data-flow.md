# Sơ đồ luồng dữ liệu & Fallback Ladder

---

## 1. Luồng chính — một câu hỏi từ học viên tới câu trả lời có trích dẫn

```
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 1 — PRESENTATION (frontend/)                                      │
│   Học viên nhập câu hỏi / lời giải thích teach-back                    │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ POST /api/v1/chat  { question, history }
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 2 — API GATEWAY (src/backend/api/)                                │
│   Validate Pydantic · sinh request_id · started_at = monotonic()       │
└──────────────────────────────┬─────────────────────────────────────────┘
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TẦNG 4a — HYBRID RETRIEVER (src/core/rag_engine.py)                    │
│                                                                        │
│      Dense (Qdrant, embedding)  ──70%──┐                               │
│                                        ├──► hợp nhất & xếp hạng        │
│      Sparse (BM25, từ khoá)     ──30%──┘        → top-k chunks         │
│                                                                        │
│   Mỗi chunk mang source_id ỔN ĐỊNH: {pack}-{week}-{kind}-{lesson}#{n}  │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │ list[RetrievedChunk]
                               ▼
╔════════════════════════════════════════════════════════════════════════╗
║ TẦNG 4b — PROMPT / GUARDRAIL / FALLBACK  (src/core/prompts/)           ║
║                                                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (1) sanitize_untrusted()                     [sanitizer.py]      │  ║
║  │     NFKC → strip vô hình → strip control → gắn cờ → escape < >   │  ║
║  │     ⇒ BẢO ĐẢM: không byte dữ liệu nào phát ra được một thẻ XML   │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
║                               ▼                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (2) build_chat_prompt()                       [builders.py]      │  ║
║  │     system: <role>…<final_reminders><integrity_token>            │  ║
║  │     user:   <retrieved_documents>…<student_question><task>       │  ║
║  │     ⇒ <task> LUÔN ở cuối: mệnh lệnh thật luôn "mới hơn" mọi      │  ║
║  │        văn bản bị chèn trong tài liệu                            │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
║                               ▼                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (3) GUARDRAIL ĐẦU VÀO                        [guardrails.py]     │  ║
║  │     G1 độ dài · G2 injection CRITICAL · G3 cổng context rỗng     │  ║
║  │                                                                  │  ║
║  │     G3 fail ──────────────────────────────► KHÔNG GỌI LLM        │  ║
║  │                                              trả câu từ chối      │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
║                               ▼                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (4) FALLBACK LADDER  T0 → T5                  [fallback.py]      │  ║
║  │     xem sơ đồ mục 2                                              │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
║                               ▼                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (5) GUARDRAIL ĐẦU RA                         [guardrails.py]     │  ║
║  │     G4 schema · G5 source_id có thật · G6 excerpt nguyên văn     │  ║
║  │     G7 phải có trích dẫn · G8 canary · G9 cụm từ cấm             │  ║
║  │     G10 evidence · G11 cấu trúc quiz · G12 ngôn ngữ (cảnh báo)   │  ║
║  │                                                                  │  ║
║  │     fail ─────────────────────────────────► HẠ CẤP về T3         │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
║                               ▼                                        ║
║  ┌──────────────────────────────────────────────────────────────────┐  ║
║  │ (6) hydrate_citations() → success_envelope()                     │  ║
║  │     title tra cứu từ chunk gốc, KHÔNG do LLM sinh                │  ║
║  │     latency_ms = monotonic(), không dùng wall-clock              │  ║
║  └────────────────────────────┬─────────────────────────────────────┘  ║
╚═══════════════════════════════╪════════════════════════════════════════╝
                                ▼
                    { success, data, error, meta }
                                │
                                ▼
                   [ Frontend render + trích dẫn ]
```

---

## 2. Fallback Ladder

Deadline toàn cục **10 giây** cho cả pha generation. Mỗi tier nhận `min(ngân_sách_tier, thời_gian_còn_lại)` — nhờ vậy vẫn retry và vẫn đổi provider được mà không bao giờ vượt trần.

```
                          ┌─────────────────────┐
                          │  T0  Gemini  6.0s   │
                          └──────────┬──────────┘
                    thành công       │       lỗi
              ┌──────────────────────┴───────────────────┐
              ▼                                          ▼
     ┌─────────────────┐                    ┌────────────────────────┐
     │ parse JSON?     │                    │ lỗi có retryable không?│
     └────┬───────┬────┘                    └──────┬──────────┬──────┘
       ok │       │ hỏng                   có      │          │ không
          │       ▼                                │          │  (401/403,
          │  ┌──────────────────────┐              │          │   safety)
          │  │ T1.5a sửa bằng CODE  │              ▼          │
          │  │  (0ms, miễn phí)     │   ┌──────────────────┐  │
          │  └───┬──────────┬───────┘   │ T1 retry  3.0s   │  │
          │   ok │          │ vẫn hỏng  │ cùng provider    │  │
          │      │          ▼           └────────┬─────────┘  │
          │      │  ┌───────────────────┐        │            │
          │      │  │ T1.5b gọi LLM sửa │        │            │
          │      │  │       2.5s        │        │            │
          │      │  └────┬─────────┬────┘        │            │
          │      │    ok │         │ hỏng        │ vẫn lỗi    │
          ▼      ▼       ▼         ▼             ▼            ▼
     ┌────────────────────────┐   ┌────────────────────────────────┐
     │  GUARDRAIL ĐẦU RA      │   │  T2  OpenAI  4.0s              │
     │  G4–G12                │   │  DÙNG NGUYÊN PromptBundle —    │
     └────┬──────────────┬────┘   │  0 dòng prompt phải viết lại   │
       ok │              │ fail   └───────────┬────────────────────┘
          │              │                    │ vẫn lỗi
          ▼              ▼                    ▼
  ┌──────────────┐   ┌──────────────────────────────────────────┐
  │ success:true │   │ còn chunk không?                         │
  │ degraded:    │   └──────┬──────────────────────┬────────────┘
  │   false      │      có  │                      │ không
  └──────────────┘          ▼                      ▼
                  ┌────────────────────┐  ┌──────────────────────┐
                  │ T3 TRÍCH XUẤT      │  │ T4 câu từ chối       │
                  │ ghép từ chunk,     │  │ cố định, không LLM   │
                  │ KHÔNG gọi LLM      │  └──────────┬───────────┘
                  │ → vẫn CÓ trích dẫn │             │
                  └──────────┬─────────┘             │
                             ▼                       ▼
                     ┌────────────────────────────────────┐
                     │ success: true, degraded: true      │
                     │ meta.degraded_reason = <ErrorCode> │
                     └────────────────────────────────────┘

  T5 (success: false) CHỈ dùng khi: đầu vào bị chặn, canary rò rỉ,
  config hỏng, hoặc exception không lường trước.
```

### Vì sao ưu tiên hạ cấp hơn báo lỗi

Frontend hiện **không có một dòng xử lý lỗi nào** — envelope `error` render ra khoảng trắng, còn degraded success render ra chữ. Người dùng thấy một câu trả lời có nguồn vẫn tốt hơn thấy một màn hình trắng.

### Vì sao không retry 401/403

Retry một lỗi xác thực chỉ đốt deadline cho một lần fail chắc chắn. Thời gian đó nên dành cho tier T2 (đổi provider) hoặc T3 (trả lời trích xuất).

---

## 3. Luồng teach-back — lát cắt CP1

```
Học viên tự giải thích khái niệm (văn bản tự do, không nhìn tài liệu)
        │
        │  ⚠️ Đây là đầu vào RỦI RO NHẤT của cả sản phẩm:
        │     tự do, dài, do người dùng nhập.
        ▼
sanitize_untrusted(max_chars=3000)  →  cùng bộ lọc như tài liệu truy xuất
        ▼
build_teach_back_prompt()
        │   <transcript_excerpts> → <rubric_criteria>
        │   → <concept_under_review> → <student_explanation> → <task>
        ▼
LLM → TeachBackDiagnosis
        │
        │   verdict ∈ { GAP_FOUND, NEEDS_MORE_EVIDENCE, OFF_TOPIC }
        │                    ▲
        │                    └── KHÔNG CÓ "UNDERSTOOD".
        │                        Model không thể phát ngôn kết luận đó.
        ▼
G9  chặn ~15 cụm từ cấm ("bạn đã hiểu", "đã nắm vững", …)
G10 mỗi evidence phải có source_id thật + quote nguyên văn
        ▼
Trả về: một lỗ hổng + bằng chứng trích dẫn + một câu hỏi ngược
        ▼
Học viên bổ sung → làm trắc nghiệm
        ▼
┌───────────────────────────────────────────────────────────────┐
│  CHỈ phép so khớp trắc nghiệm DETERMINISTIC ở frontend        │
│  mới được lật trạng thái chủ đề sang "Đã ôn & xác nhận".      │
│  Hợp đồng backend không có đường nào cho LLM chạm vào đó.     │
└───────────────────────────────────────────────────────────────┘
```

Ba tầng cưỡng chế luật "AI không kết luận học viên đã hiểu" — lược đồ, từ vựng, hệ thống — được mô tả đầy đủ trong [spec.md](../spec.md) mục 2 và [PROMPT_SPEC.md](PROMPT_SPEC.md) mục 2.2.
