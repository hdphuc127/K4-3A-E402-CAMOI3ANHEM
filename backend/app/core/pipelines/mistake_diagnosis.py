from __future__ import annotations

import asyncio
import time

from app.core.citation.source_citation import build_source_citation
from app.core.config import settings
from app.core.llm.client import default_llm_caller
from app.core.prompts import build_chat_prompt, run_guarded_generation
from app.core.prompts.mistake_diagnosis_prompt import (
    MISTAKE_DIAGNOSIS_SYSTEM_PROMPT,
)
from app.core.prompts.schemas import RetrievedChunk
from app.core.vector_search.retriever import retrieve_tokenization_context
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResult, SourceCitation

# Score assigned to the single fixture chunk until real retrieval (with a real
# similarity score) replaces retrieve_tokenization_context().
_FIXTURE_RETRIEVAL_SCORE = 0.9


def diagnose_mistake(request: DiagnosisRequest) -> DiagnosisResult:
    """Diagnose a learner's mistake on the CP3 tokenization question.

    Misconception classification stays rule-based: this endpoint only ever
    sees one lesson with three known answer patterns, so a fixed Literal
    output is more reliable than asking a model to classify it. The tutoring
    hint, however, is generated through the guarded LLM pipeline
    (app.core.prompts) when a provider key is configured, and falls back to
    the canned hint whenever the LLM is unavailable or its answer can't be
    grounded in the retrieved context.
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

    fallback_citation = build_source_citation(
        source_id=context["source_id"],
        title=context["title"],
        excerpt=context["excerpt"],
        confidence=confidence,
    )

    hint, citations = _generate_guarded_hint(
        request=request,
        misconception=misconception,
        context=context,
        fallback_hint=hint,
        fallback_citation=fallback_citation,
    )

    return DiagnosisResult(
        question_id=request.question_id,
        is_correct=misconception == "answer_is_correct",
        misconception=misconception,
        hint=hint,
        next_action=next_action,
        citations=citations,
        debug_prompt_name=MISTAKE_DIAGNOSIS_SYSTEM_PROMPT.name,
    )


def _generate_guarded_hint(
    *,
    request: DiagnosisRequest,
    misconception: str,
    context: dict[str, str],
    fallback_hint: str,
    fallback_citation: SourceCitation,
) -> tuple[str, list[SourceCitation]]:
    """Try to author the hint with a real LLM call, guarded end-to-end.

    Never raises: any failure (no API key, provider outage, guardrail
    rejection) falls back to the deterministic hint above, matching the
    fallback ladder's own "degrade, don't error" policy.
    """
    chunk = RetrievedChunk(
        source_id=context["source_id"],
        title=context["title"],
        text=context["excerpt"],
        score=_FIXTURE_RETRIEVAL_SCORE,
    )
    question = (
        f'Hoc vien duoc hoi: "{request.question_text}". Dap an dung la '
        f'"{request.correct_answer}". Hoc vien tra loi "{request.student_answer}" '
        f'va he thong xac dinh day la truong hop "{misconception}". Hay giai '
        "thich ngan gon vi sao cau tra loi co the sai va goi y huong khac phuc, "
        "khong tiet lo truc tiep dap an dung."
    )
    bundle = build_chat_prompt(question, [chunk], request_id=request.question_id)

    try:
        envelope = asyncio.run(
            run_guarded_generation(
                bundle,
                call_llm=default_llm_caller,
                chunks=[chunk],
                request_id=request.question_id,
                started_at=time.monotonic(),
                providers=(settings.llm_primary_provider, settings.llm_fallback_provider),
                deadline_s=settings.llm_deadline_s,
                enable_llm_judge=settings.enable_llm_judge,
            )
        )
    except Exception:  # noqa: BLE001 - LLM layer must never break diagnosis
        return fallback_hint, [fallback_citation]

    if envelope["success"] and not envelope["meta"].get("degraded", False):
        answer = str(envelope["data"].get("answer", "")).strip()
        raw_citations = envelope["data"].get("citations", [])
        if answer and raw_citations:
            return answer, [SourceCitation(**c) for c in raw_citations]

    return fallback_hint, [fallback_citation]
