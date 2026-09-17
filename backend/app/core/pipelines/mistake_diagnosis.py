from app.core.citation.source_citation import build_source_citation
from app.core.prompts.mistake_diagnosis_prompt import (
    MISTAKE_DIAGNOSIS_SYSTEM_PROMPT,
)
from app.core.vector_search.retriever import retrieve_tokenization_context
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult


def diagnose_mistake(request: DiagnosisRequest) -> DiagnosisResult:
    """Return a deterministic CP3-ready diagnosis placeholder.

    The function shape mirrors the future LLM/RAG pipeline:
    request -> retrieve context -> prompt -> diagnosis -> citation.
    Replace the rule block with a real LLM call when API keys are available.
    """
    context = retrieve_tokenization_context(request.lesson_id)
    normalized_answer = request.student_answer.strip().lower()

    if normalized_answer in {"3", "three", "ba"}:
        misconception = "answer_is_correct"
        hint = "Dap an dung. Hay noi lai vi sao co 3 don vi duoc tach bang khoang trang."
        next_action = "explain_reasoning"
        confidence = 0.86
    elif normalized_answer in {"8", "7", "6"}:
        misconception = "counting_characters_or_spaces"
        hint = (
            "Ban co ve dang dem ky tu hoac ca dau cach. Hay tach cau thanh "
            "cac cum lien tiep khong co khoang trang roi dem cac cum do."
        )
        next_action = "retry_answer"
        confidence = 0.78
    else:
        misconception = "ambiguous_or_unknown"
        hint = (
            "Cau tra loi chua du ro de chan doan chac chan. Hay viet cach ban "
            "dem tung don vi trong cau."
        )
        next_action = "ask_for_reasoning"
        confidence = 0.52

    citation = build_source_citation(
        source_id=context["source_id"],
        title=context["title"],
        excerpt=context["excerpt"],
        confidence=confidence,
    )

    return DiagnosisResult(
        question_id=request.question_id,
        is_correct=misconception == "answer_is_correct",
        misconception=misconception,
        hint=hint,
        next_action=next_action,
        citations=[citation],
        debug_prompt_name=MISTAKE_DIAGNOSIS_SYSTEM_PROMPT.name,
    )
