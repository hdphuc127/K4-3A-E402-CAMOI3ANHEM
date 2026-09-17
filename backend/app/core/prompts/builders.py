"""Dựng prompt từ dữ liệu đã truy xuất.

Module này chỉ chứa logic lắp ghép. Toàn bộ văn bản prompt nằm trong
``templates/`` — quy tắc THỰC THI & QUY TẮC VIBECODING mục 4.3, được test
``test_no_long_string_literals_in_logic_modules`` cưỡng chế.

Bất biến quan trọng nhất của module: **mọi văn bản không đáng tin đều đi qua
``sanitize_untrusted()`` TRƯỚC khi được nội suy vào template**. Sau bước đó,
không chuỗi nào trong dữ liệu có thể chứa ``<`` hay ``>``, nên không tài liệu
nào thoát ra khỏi thẻ của chính nó được. Test
``test_malicious_chunk_cannot_break_out_of_its_tag`` khoá điều này lại.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping, Sequence
from typing import Any

from app.core.prompts.sanitizer import Severity, sanitize_untrusted
from app.core.prompts.schemas import (
    ChatAnswer,
    FaithfulnessReport,
    PromptBundle,
    QuizSet,
    RetrievedChunk,
    RubricCriterion,
    TeachBackDiagnosis,
    coerce_chunks,
    coerce_rubric,
)
from app.core.prompts.templates import chat_rag, faithfulness, quiz_gen, shared
from app.core.prompts.templates import teach_back as teach_back_tpl

__all__ = [
    "MAX_QUESTION_CHARS",
    "MAX_EXPLANATION_CHARS",
    "build_chat_prompt",
    "build_teach_back_prompt",
    "build_quiz_prompt",
    "build_faithfulness_prompt",
    "build_repair_prompt",
]

# Giới hạn đầu vào (guardrail G1).
MAX_QUESTION_CHARS = 1000
MAX_EXPLANATION_CHARS = 3000
MAX_CHUNK_CHARS = 2000
MAX_ANSWER_REVIEW_CHARS = 4000

MIN_QUIZ_ITEMS = 3
MAX_QUIZ_ITEMS = 5

_TEMPERATURE_FACTUAL = 0.2
_TEMPERATURE_CREATIVE = 0.4
_TEMPERATURE_JUDGE = 0.0

_MAX_TOKENS_CHAT = 1200
_MAX_TOKENS_TEACH_BACK = 1400
_MAX_TOKENS_QUIZ = 2600
_MAX_TOKENS_JUDGE = 1800

_ERR_INPUT_EMPTY = "INPUT_EMPTY"
_ERR_INPUT_TOO_LONG = "INPUT_TOO_LONG"
_ERR_INJECTION = "PROMPT_INJECTION_BLOCKED"


def _make_canary() -> str:
    """Sinh tripwire cho mỗi request.

    Biến câu hỏi "system prompt có bị rò rỉ không" thành một phép tìm chuỗi
    chính xác thay vì một phán đoán mơ hồ (guardrail G8).
    """
    return f"VLRN-{secrets.token_hex(8)}"


def _render_documents(chunks: Sequence[RetrievedChunk]) -> str:
    if not chunks:
        return shared.EMPTY_DOCUMENTS_PLACEHOLDER
    rendered = []
    for chunk in chunks:
        rendered.append(
            shared.DOCUMENT_TEMPLATE.format(
                source_id=sanitize_untrusted(chunk.source_id, max_chars=200).text,
                title=sanitize_untrusted(chunk.title, max_chars=200).text,
                locator=sanitize_untrusted(chunk.locator(), max_chars=100).text,
                score=chunk.score,
                content=sanitize_untrusted(chunk.text, max_chars=MAX_CHUNK_CHARS).text,
            )
        )
    return "\n".join(rendered)


def _render_history(history: Sequence[tuple[str, str]]) -> str:
    if not history:
        return shared.EMPTY_HISTORY_PLACEHOLDER
    rendered = []
    for role, text in history:
        safe_role = "user" if role == "user" else "assistant"
        rendered.append(
            shared.HISTORY_TURN_TEMPLATE.format(
                role=safe_role,
                text=sanitize_untrusted(text, max_chars=800).text,
            )
        )
    return "\n".join(rendered)


def _render_rubric(rubric: Sequence[RubricCriterion]) -> str:
    if not rubric:
        return shared.EMPTY_RUBRIC_PLACEHOLDER
    return "\n".join(
        shared.RUBRIC_CRITERION_TEMPLATE.format(
            rubric_id=sanitize_untrusted(item.rubric_id, max_chars=100).text,
            weight=item.weight,
            description=sanitize_untrusted(item.description, max_chars=400).text,
        )
        for item in rubric
    )


def _render_list(values: Sequence[str], empty_marker: str) -> str:
    if not values:
        return f"  <none>{empty_marker}</none>"
    return "\n".join(
        f"  <item>{sanitize_untrusted(v, max_chars=300).text}</item>" for v in values
    )


def _check_input(raw: str, *, max_chars: int) -> tuple[str, str, tuple[str, ...], int]:
    """Guardrail G1 + G2 cho một trường đầu vào tự do.

    Trả về ``(text_da_lam_sach, ma_loi, flags, severity)``. Không raise: lỗi
    được mang theo trong PromptBundle để tầng orchestration dựng envelope.
    """
    if not raw or not raw.strip():
        return "", _ERR_INPUT_EMPTY, (), 0
    if len(raw) > max_chars:
        return "", _ERR_INPUT_TOO_LONG, (), 0

    result = sanitize_untrusted(raw, max_chars=max_chars)
    flags = tuple(sorted(str(f) for f in result.flags))
    # Học viên hỏi xin system prompt không phải một câu hỏi ôn tập. Chặn ngay
    # tại đây tiết kiệm trọn deadline 10 giây và một lượt gọi API.
    error = _ERR_INJECTION if result.severity >= Severity.CRITICAL else ""
    return result.text, error, flags, int(result.severity)


def _bundle(
    *,
    system: str,
    user: str,
    response_model: type,
    temperature: float,
    max_output_tokens: int,
    chunks: Sequence[RetrievedChunk],
    canary: str,
    task: str,
    input_error: str = "",
    input_flags: tuple[str, ...] = (),
    input_severity: int = 0,
) -> PromptBundle:
    index: Mapping[str, RetrievedChunk] = {c.source_id: c for c in chunks}
    return PromptBundle(
        system=system,
        user=user,
        response_model=response_model,  # type: ignore[arg-type]
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        allowed_source_ids=tuple(index.keys()),
        chunk_index=index,
        canary=canary,
        task=task,  # type: ignore[arg-type]
        input_error=input_error,
        input_flags=input_flags,
        input_severity=input_severity,
    )


def build_chat_prompt(
    question: str,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    *,
    history: Sequence[tuple[str, str]] = (),
    lesson_label: str | None = None,
    request_id: str = "",
) -> PromptBundle:
    """Prompt hỏi đáp RAG có trích dẫn."""
    del lesson_label, request_id  # nhận để giữ chữ ký ổn định, chưa dùng tới

    items = coerce_chunks(chunks)
    canary = _make_canary()
    safe_question, error, flags, severity = _check_input(
        question, max_chars=MAX_QUESTION_CHARS
    )

    system = chat_rag.CHAT_RAG_SYSTEM_PROMPT.format(
        untrusted_content_policy=shared.UNTRUSTED_CONTENT_POLICY,
        language_policy=shared.LANGUAGE_POLICY,
        integrity_token=shared.INTEGRITY_TOKEN_BLOCK.format(canary=canary),
    )
    user = chat_rag.CHAT_RAG_USER_TEMPLATE.format(
        documents=_render_documents(items),
        history=_render_history(history),
        question=safe_question,
    )
    return _bundle(
        system=system,
        user=user,
        response_model=ChatAnswer,
        temperature=_TEMPERATURE_FACTUAL,
        max_output_tokens=_MAX_TOKENS_CHAT,
        chunks=items,
        canary=canary,
        task="CHAT",
        input_error=error,
        input_flags=flags,
        input_severity=severity,
    )


def build_teach_back_prompt(
    concept: str,
    student_explanation: str,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    *,
    rubric: Sequence[RubricCriterion | Mapping[str, Any]] = (),
    request_id: str = "",
) -> PromptBundle:
    """Prompt chẩn đoán lỗ hổng kiến thức — lát cắt CP1.

    ``student_explanation`` là đầu vào rủi ro nhất của cả sản phẩm: văn bản tự
    do, dài, do người dùng nhập. Nó đi qua đúng bộ lọc như tài liệu truy xuất,
    cộng thêm giới hạn 3000 ký tự.
    """
    del request_id

    items = coerce_chunks(chunks)
    criteria = coerce_rubric(rubric)
    canary = _make_canary()
    safe_explanation, error, flags, severity = _check_input(
        student_explanation, max_chars=MAX_EXPLANATION_CHARS
    )

    system = teach_back_tpl.TEACH_BACK_SYSTEM_PROMPT.format(
        untrusted_content_policy=shared.UNTRUSTED_CONTENT_POLICY,
        language_policy=shared.LANGUAGE_POLICY,
        integrity_token=shared.INTEGRITY_TOKEN_BLOCK.format(canary=canary),
    )
    user = teach_back_tpl.TEACH_BACK_USER_TEMPLATE.format(
        documents=_render_documents(items),
        rubric=_render_rubric(criteria),
        concept=sanitize_untrusted(concept, max_chars=300).text,
        explanation=safe_explanation,
    )
    return _bundle(
        system=system,
        user=user,
        response_model=TeachBackDiagnosis,
        temperature=_TEMPERATURE_FACTUAL,
        max_output_tokens=_MAX_TOKENS_TEACH_BACK,
        chunks=items,
        canary=canary,
        task="TEACH_BACK",
        input_error=error,
        input_flags=flags,
        input_severity=severity,
    )


def build_quiz_prompt(
    topic: str,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    *,
    num_items: int = 4,
    weak_points: Sequence[str] = (),
    difficulty: str = "MEDIUM",
    request_id: str = "",
) -> PromptBundle:
    """Prompt sinh 3-5 câu trắc nghiệm thích ứng."""
    del request_id

    items = coerce_chunks(chunks)
    canary = _make_canary()
    count = max(MIN_QUIZ_ITEMS, min(MAX_QUIZ_ITEMS, num_items))
    level = difficulty if difficulty in ("EASY", "MEDIUM", "HARD") else "MEDIUM"

    system = quiz_gen.QUIZ_GEN_SYSTEM_PROMPT.format(
        num_items=count,
        difficulty=level,
        untrusted_content_policy=shared.UNTRUSTED_CONTENT_POLICY,
        language_policy=shared.LANGUAGE_POLICY,
        integrity_token=shared.INTEGRITY_TOKEN_BLOCK.format(canary=canary),
    )
    user = quiz_gen.QUIZ_GEN_USER_TEMPLATE.format(
        documents=_render_documents(items),
        weak_points=_render_list(weak_points, "Chưa ghi nhận điểm yếu cụ thể."),
        topic=sanitize_untrusted(topic, max_chars=300).text,
        num_items=count,
    )
    return _bundle(
        system=system,
        user=user,
        response_model=QuizSet,
        temperature=_TEMPERATURE_CREATIVE,
        max_output_tokens=_MAX_TOKENS_QUIZ,
        chunks=items,
        canary=canary,
        task="QUIZ",
    )


def build_faithfulness_prompt(
    answer_text: str,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    *,
    request_id: str = "",
) -> PromptBundle:
    """Prompt judge chấm độ trung thực, dùng chung cho guardrail và eval."""
    del request_id

    items = coerce_chunks(chunks)
    canary = _make_canary()

    system = faithfulness.FAITHFULNESS_SYSTEM_PROMPT.format(
        integrity_token=shared.INTEGRITY_TOKEN_BLOCK.format(canary=canary),
    )
    user = faithfulness.FAITHFULNESS_USER_TEMPLATE.format(
        documents=_render_documents(items),
        answer=sanitize_untrusted(answer_text, max_chars=MAX_ANSWER_REVIEW_CHARS).text,
    )
    return _bundle(
        system=system,
        user=user,
        response_model=FaithfulnessReport,
        temperature=_TEMPERATURE_JUDGE,
        max_output_tokens=_MAX_TOKENS_JUDGE,
        chunks=items,
        canary=canary,
        task="JUDGE",
    )


def build_repair_prompt(
    broken_output: str,
    original: PromptBundle,
    violations: Sequence[str],
) -> PromptBundle:
    """Prompt sửa định dạng — tier T1.5b của fallback ladder.

    Giữ nguyên ``response_model``, ``allowed_source_ids`` và ``chunk_index`` của
    bundle gốc, để mọi guardrail chạy lại trên kết quả sửa vẫn đối chiếu đúng
    tập tài liệu ban đầu.
    """
    from app.core.prompts.schema_compat import to_gemini_schema

    schema_text = str(to_gemini_schema(original.response_model))
    user = shared.REPAIR_USER_TEMPLATE.format(
        broken=sanitize_untrusted(broken_output, max_chars=3000).text,
        schema=schema_text,
        violations=_render_list(list(violations), "Sai định dạng JSON."),
    )
    return PromptBundle(
        system=shared.REPAIR_SYSTEM_PROMPT,
        user=user,
        response_model=original.response_model,
        temperature=_TEMPERATURE_JUDGE,
        max_output_tokens=original.max_output_tokens,
        allowed_source_ids=original.allowed_source_ids,
        chunk_index=original.chunk_index,
        canary=original.canary,
        task=original.task,
    )
