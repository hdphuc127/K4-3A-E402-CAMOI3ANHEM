"""System Prompts, Guardrails & Fallback — Adaptive VLearn AI Assistant.

Đây là bề mặt public DUY NHẤT của tầng này. Mọi thứ khác trong package là chi
tiết cài đặt và có thể thay đổi.

HỢP ĐỒNG — phần này đóng băng sau khi bàn giao
----------------------------------------------
``src/core/rag_engine.py`` và các route FastAPI chỉ import từ đây::

    from src.core.prompts import build_chat_prompt, run_guarded_generation

Route chat đầy đủ gọn trong khoảng 12 dòng::

    started_at = time.monotonic()
    request_id = f"req-{uuid4().hex[:12]}"
    chunks = await hybrid_search(req.question, top_k=6)     # code cua Hoa
    bundle = build_chat_prompt(req.question, chunks, request_id=request_id)
    return await run_guarded_generation(
        bundle, call_llm=gemini_client, chunks=chunks,
        request_id=request_id, started_at=started_at,
    )

Hai điểm khiến hợp đồng này không va chạm với module của người khác:

1. Mọi hàm nhận ``RetrievedChunk | Mapping[str, Any]`` và tự ``model_validate``
   bên trong. Truyền thẳng dict payload từ Qdrant được, không ai bị ép import
   type của ai.
2. ``LlmCaller`` là một ``Protocol``. Package này KHÔNG import SDK LLM nào, nên
   toàn bộ test của nó chạy trong venv chỉ có pydantic + pytest.

``run_guarded_generation`` không bao giờ raise — mọi nhánh lỗi đều kết thúc bằng
một envelope hợp lệ, nên route không cần lấy một khối try/except nào.

GHI CHÚ KIẾN TRÚC (ADR-004)
---------------------------
``src/core/prompts`` là một package chứ không phải file ``prompts.py``. Đường
import ``from src.core.prompts import ...`` phân giải y hệt nhau, nên mọi đoạn
code viết theo cách gọi trong ``Modules.md`` vẫn chạy; đồng thời thoả mãn yêu
cầu thư mục ``src/core/prompts/`` của ``ARCHITECTUREs.md`` mục 1.
"""

from src.core.prompts.builders import (
    MAX_EXPLANATION_CHARS,
    MAX_QUESTION_CHARS,
    build_chat_prompt,
    build_faithfulness_prompt,
    build_quiz_prompt,
    build_repair_prompt,
    build_teach_back_prompt,
)
from src.core.prompts.fallback import (
    ERROR_CATALOG,
    LLM_DEADLINE_S,
    ErrorCode,
    ErrorSpec,
    error_envelope,
    message_for,
    redact,
    repair_json_text,
    run_guarded_generation,
    score_faithfulness,
    success_envelope,
)
from src.core.prompts.guardrails import (
    MIN_RETRIEVAL_SCORE,
    GuardrailReport,
    excerpt_containment,
    finalize_faithfulness,
    has_retrieval_context,
)
from src.core.prompts.sanitizer import (
    InjectionFlag,
    SanitizedText,
    Severity,
    sanitize_untrusted,
)
from src.core.prompts.schema_compat import (
    UnsupportedSchemaError,
    to_gemini_schema,
    to_openai_response_format,
)
from src.core.prompts.schemas import (
    ChatAnswer,
    Citation,
    CitationDraft,
    ClaimVerdict,
    Evidence,
    FaithfulnessReport,
    LlmCaller,
    PromptBundle,
    Provider,
    QuizItem,
    QuizSet,
    RetrievedChunk,
    RubricCriterion,
    TeachBackDiagnosis,
)

__all__ = [
    # --- dung prompt ---
    "build_chat_prompt",
    "build_teach_back_prompt",
    "build_quiz_prompt",
    "build_faithfulness_prompt",
    "build_repair_prompt",
    # --- dieu phoi: guardrail + fallback + envelope trong mot lenh ---
    "run_guarded_generation",
    # --- kieu du lieu ---
    "PromptBundle",
    "RetrievedChunk",
    "RubricCriterion",
    "Provider",
    "LlmCaller",
    "ChatAnswer",
    "Citation",
    "CitationDraft",
    "TeachBackDiagnosis",
    "Evidence",
    "QuizItem",
    "QuizSet",
    "ClaimVerdict",
    "FaithfulnessReport",
    # --- envelope ---
    "success_envelope",
    "error_envelope",
    "ErrorCode",
    "ErrorSpec",
    "ERROR_CATALOG",
    "message_for",
    "redact",
    "repair_json_text",
    "LLM_DEADLINE_S",
    # --- danh gia, dung cho tests/eval_metrics.py (M4) ---
    "score_faithfulness",
    "finalize_faithfulness",
    # --- guardrail dung rieng le neu can ---
    "GuardrailReport",
    "has_retrieval_context",
    "excerpt_containment",
    "MIN_RETRIEVAL_SCORE",
    "MAX_QUESTION_CHARS",
    "MAX_EXPLANATION_CHARS",
    # --- sanitizer ---
    "sanitize_untrusted",
    "SanitizedText",
    "InjectionFlag",
    "Severity",
    # --- tuong thich provider ---
    "to_gemini_schema",
    "to_openai_response_format",
    "UnsupportedSchemaError",
]
