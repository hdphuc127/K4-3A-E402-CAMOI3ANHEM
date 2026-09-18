"""Toàn bộ văn bản tiếng Việt hiển thị cho học viên.

Gom về một chỗ vì ba lý do:

1. Quy tắc THỰC THI mục 4.3 — tách văn bản khỏi logic code.
2. Văn phong nhất quán: mọi thông báo đều xưng "mình", gọi "bạn", nói được nên
   làm gì tiếp theo, và không đổ lỗi cho học viên.
3. Test ``test_every_error_code_has_vietnamese_message`` duyệt hết ``ErrorCode``
   và fail build nếu có mã lỗi nào thiếu thông điệp ở đây — không ai thêm được
   mã lỗi mà quên viết câu thông báo.

Nguyên tắc viết: nói điều đã xảy ra ở phía hệ thống, rồi nói bạn nên làm gì.
Không dùng từ kỹ thuật (timeout, rate limit, schema), không xin lỗi dài dòng.
"""

# Khoá là giá trị của ErrorCode. Xem fallback.py.
ERROR_MESSAGES_VI: dict[str, str] = {
    "LLM_TIMEOUT": (
        "Hệ thống chưa kịp trả lời trong thời gian cho phép. "
        "Bạn thử hỏi lại giúp mình nhé."
    ),
    "LLM_RATE_LIMITED": (
        "Hệ thống đang có nhiều người dùng cùng lúc. "
        "Bạn chờ khoảng 30 giây rồi thử lại nhé."
    ),
    "LLM_UNAVAILABLE": (
        "Trợ lý AI đang tạm thời gián đoạn. Bạn thử lại sau ít phút nhé."
    ),
    "LLM_AUTH_ERROR": (
        "Hệ thống đang gặp sự cố cấu hình. Bạn báo giúp nhóm phát triển nhé."
    ),
    "LLM_CONTENT_BLOCKED": (
        "Nội dung này mình chưa hỗ trợ trả lời. Bạn thử diễn đạt theo cách khác nhé."
    ),
    "LLM_INVALID_JSON": (
        "Mình chưa tạo được câu trả lời đúng định dạng. Bạn thử hỏi lại nhé."
    ),
    "SCHEMA_VALIDATION_FAILED": (
        "Mình chưa tạo được câu trả lời đúng định dạng. Bạn thử hỏi lại nhé."
    ),
    "GUARDRAIL_UNGROUNDED": (
        "Mình chưa tìm được dẫn chứng đủ chắc trong tài liệu bài giảng "
        "nên chưa trả lời phần này."
    ),
    "GUARDRAIL_NO_CITATION": (
        "Mình chưa tìm được dẫn chứng đủ chắc trong tài liệu bài giảng "
        "nên chưa trả lời phần này."
    ),
    "GUARDRAIL_FORBIDDEN_CLAIM": (
        "Mình chưa đưa ra được nhận xét có đủ căn cứ cho phần này. "
        "Bạn thử giải thích lại rõ hơn một chút nhé."
    ),
    "GUARDRAIL_QUIZ_INVALID": (
        "Mình chưa tạo đủ câu hỏi ôn tập từ phần tài liệu này. "
        "Bạn thử chọn phần khác nhé."
    ),
    "PROMPT_LEAK_DETECTED": ("Mình gặp lỗi khi tạo câu trả lời. Bạn thử hỏi lại nhé."),
    "PROMPT_INJECTION_BLOCKED": (
        "Yêu cầu này nằm ngoài phạm vi ôn tập của mình. "
        "Bạn hỏi mình về nội dung bài giảng nhé."
    ),
    "RETRIEVAL_EMPTY": (
        "Mình không tìm thấy nội dung này trong tài liệu bài giảng của khóa học."
    ),
    "RETRIEVAL_FAILED": (
        "Kho tài liệu đang tạm thời không truy cập được. Bạn thử lại sau ít phút nhé."
    ),
    "INPUT_EMPTY": "Bạn nhập câu hỏi giúp mình nhé.",
    "INPUT_TOO_LONG": ("Câu hỏi của bạn hơi dài. Bạn rút gọn lại giúp mình nhé."),
    "INTERNAL_ERROR": ("Hệ thống đang gặp lỗi. Nhóm đã ghi nhận, bạn thử lại sau nhé."),
}


# --- Tier T3: trả lời trích xuất, không gọi LLM ----------------------------
#
# Đây là tier đáng giá nhất của cả fallback ladder. Thay vì một lời xin lỗi, ta
# ghép câu trả lời thật từ phần retrieval đã trả tiền rồi. Nó grounded THEO CẤU
# TRÚC - văn bản được copy nguyên từ chunk - nên tiêu chí DoD "mọi câu trả lời
# kèm dẫn nguồn" vẫn giữ được ngay cả khi hệ thống đang hạ cấp.

EXTRACTIVE_FALLBACK_TEMPLATE = """\
Mình chưa tạo được câu trả lời hoàn chỉnh, nhưng đây là đoạn tài liệu liên quan \
nhất tới câu hỏi của bạn:

> {excerpt}

Nguồn: {title} — {locator}. Bạn mở nguồn để đọc đầy đủ nhé."""

EXTRACTIVE_FALLBACK_EXCERPT_CHARS = 400


# --- Từ chối trong luồng chat (G13) -----------------------------------------
#
# Câu mở đầu là bắt buộc theo <refusal_policy> trong chat_rag.py, nhưng phần
# gợi ý "nên tìm ở đâu" phía sau đó là văn bản tự do của model — không có gì
# buộc nó chỉ nhắc tên tài liệu có thật. Để field đó do CODE dựng từ chunk
# thật thay vì tin lời model, xoá hẳn một lớp hallucination (model đã từng
# bịa ra một kỹ thuật không tồn tại trong bất kỳ tài liệu nào).

CHAT_REFUSAL_WITH_HINT_TEMPLATE = (
    "Mình không tìm thấy nội dung này trong tài liệu bài giảng của khóa học. "
    "Tài liệu gần nhất mình có là {title}, bạn thử xem lại ở đó nhé."
)

CHAT_REFUSAL_NO_CONTEXT = (
    "Mình không tìm thấy nội dung này trong tài liệu bài giảng của khóa học."
)


# --- Kiến thức mở rộng ngoài tài liệu (G14) ---------------------------------
#
# Khi model mở rộng bằng kiến thức chuyên môn (general_knowledge_used=true),
# nhãn "đây là phần ngoài tài liệu" do CODE gắn thay vì tin model tự khai báo
# đúng — cùng lý do với CHAT_REFUSAL_WITH_HINT_TEMPLATE ở trên.

GENERAL_KNOWLEDGE_DISCLAIMER = (
    "\n\n_(Phần trên là kiến thức chung ngoài tài liệu bài giảng của khóa học, "
    "không có trích dẫn cụ thể — bạn nên đối chiếu thêm nếu cần chính xác "
    "tuyệt đối.)_"
)
