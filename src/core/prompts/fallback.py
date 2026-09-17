"""Bảng mã lỗi, response envelope và fallback ladder.

DEADLINE, KHÔNG PHẢI TIMEOUT RỜI RẠC
------------------------------------
``CODING_STANDARDS.md`` mục 2 yêu cầu timeout 10 giây cho lời gọi LLM. Ở đây 10
giây được hiểu là **deadline toàn cục cho cả pha generation**: mỗi tier nhận
``min(ngân_sách_tier, thời_gian_còn_lại)``. Nhờ vậy vẫn retry và vẫn đổi
provider được, mà không lần gọi nào và không tổng nào vượt 10 giây.

CHÍNH SÁCH: HẠ CẤP, KHÔNG BÁO LỖI
---------------------------------
Ưu tiên T3/T4 (``success: true`` + ``meta.degraded``) hơn T5 (``success:
false``). Lý do đã kiểm chứng trong code: frontend hiện tại không có một dòng
xử lý lỗi nào, nên envelope ``error`` render ra khoảng trắng, còn degraded
success render ra chữ. Chỉ dùng ``success: false`` khi thực sự không có gì để
hiển thị.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ValidationError

from src.core.prompts import guardrails
from src.core.prompts.builders import build_faithfulness_prompt, build_repair_prompt
from src.core.prompts.schemas import (
    ChatAnswer,
    Citation,
    FaithfulnessReport,
    LlmCaller,
    PromptBundle,
    Provider,
    QuizSet,
    RetrievedChunk,
    RubricCriterion,
    TeachBackDiagnosis,
    coerce_chunks,
    coerce_rubric,
)
from src.core.prompts.templates.messages import (
    ERROR_MESSAGES_VI,
    EXTRACTIVE_FALLBACK_EXCERPT_CHARS,
    EXTRACTIVE_FALLBACK_TEMPLATE,
)

__all__ = [
    "ErrorCode",
    "ErrorSpec",
    "ERROR_CATALOG",
    "LLM_DEADLINE_S",
    "redact",
    "repair_json_text",
    "success_envelope",
    "error_envelope",
    "run_guarded_generation",
    "score_faithfulness",
]


class ErrorCode(StrEnum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_AUTH_ERROR = "LLM_AUTH_ERROR"
    LLM_CONTENT_BLOCKED = "LLM_CONTENT_BLOCKED"
    LLM_INVALID_JSON = "LLM_INVALID_JSON"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    GUARDRAIL_UNGROUNDED = "GUARDRAIL_UNGROUNDED"
    GUARDRAIL_NO_CITATION = "GUARDRAIL_NO_CITATION"
    GUARDRAIL_FORBIDDEN_CLAIM = "GUARDRAIL_FORBIDDEN_CLAIM"
    GUARDRAIL_QUIZ_INVALID = "GUARDRAIL_QUIZ_INVALID"
    PROMPT_LEAK_DETECTED = "PROMPT_LEAK_DETECTED"
    PROMPT_INJECTION_BLOCKED = "PROMPT_INJECTION_BLOCKED"
    RETRIEVAL_EMPTY = "RETRIEVAL_EMPTY"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    INPUT_EMPTY = "INPUT_EMPTY"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True, slots=True)
class ErrorSpec:
    """Thuoc tinh ky thuat cua mot ma loi.

    Thong diep tieng Viet KHONG nam o day ma o
    ``templates/messages.ERROR_MESSAGES_VI`` - tra cuu bang ``message_for()``.
    Tach ra vi moi van ban hien thi cho hoc vien deu phai nam trong templates/.
    """

    http_status: int
    retryable: bool


ERROR_CATALOG: dict[ErrorCode, ErrorSpec] = {
    ErrorCode.LLM_TIMEOUT: ErrorSpec(504, True),
    ErrorCode.LLM_RATE_LIMITED: ErrorSpec(429, True),
    ErrorCode.LLM_UNAVAILABLE: ErrorSpec(503, True),
    ErrorCode.LLM_AUTH_ERROR: ErrorSpec(500, False),
    ErrorCode.LLM_CONTENT_BLOCKED: ErrorSpec(422, False),
    ErrorCode.LLM_INVALID_JSON: ErrorSpec(502, True),
    ErrorCode.SCHEMA_VALIDATION_FAILED: ErrorSpec(502, True),
    ErrorCode.GUARDRAIL_UNGROUNDED: ErrorSpec(200, False),
    ErrorCode.GUARDRAIL_NO_CITATION: ErrorSpec(200, False),
    ErrorCode.GUARDRAIL_FORBIDDEN_CLAIM: ErrorSpec(200, False),
    ErrorCode.GUARDRAIL_QUIZ_INVALID: ErrorSpec(200, False),
    ErrorCode.PROMPT_LEAK_DETECTED: ErrorSpec(502, False),
    ErrorCode.PROMPT_INJECTION_BLOCKED: ErrorSpec(400, False),
    ErrorCode.RETRIEVAL_EMPTY: ErrorSpec(200, False),
    ErrorCode.RETRIEVAL_FAILED: ErrorSpec(503, True),
    ErrorCode.INPUT_EMPTY: ErrorSpec(400, False),
    ErrorCode.INPUT_TOO_LONG: ErrorSpec(413, False),
    ErrorCode.INTERNAL_ERROR: ErrorSpec(500, False),
}


def message_for(code: ErrorCode) -> str:
    return ERROR_MESSAGES_VI[code.value]


# --- Ngân sách thời gian ---------------------------------------------------

LLM_DEADLINE_S = 10.0
_TIER_BUDGET_S: dict[str, float] = {"T0": 6.0, "T1": 3.0, "T1_5": 2.5, "T2": 4.0}
_MIN_BUDGET_TO_TRY_S = 1.5
_RETRY_BACKOFF_S = 0.4
_JUDGE_BUDGET_S = 6.0
_MIN_BUDGET_FOR_JUDGE_S = 2.5


# --- Che dấu thông tin nhạy cảm --------------------------------------------

_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}"
    r"|AIza[0-9A-Za-z_-]{10,}"
    r"|Bearer\s+[A-Za-z0-9._-]{8,}"
    r"|(?i:api[_-]?key|secret|token|password)\s*[=:]\s*\S+)"
)
_MAX_DETAILS_CHARS = 200


def redact(text: str) -> str:
    """Che API key trước khi bất cứ thứ gì rời khỏi server.

    ``CODING_STANDARDS.md`` mục 2: log chi tiết ở server nhưng ẩn thông tin nhạy
    cảm khỏi phản hồi trả về client. Hàm này biến quy tắc đó thành cơ chế.
    """
    return _SECRET_RE.sub("[REDACTED]", text or "")


def _classify(exc: BaseException) -> ErrorCode:
    """Suy ra mã lỗi từ exception của provider mà không import SDK nào."""
    if isinstance(exc, asyncio.TimeoutError | TimeoutError):
        return ErrorCode.LLM_TIMEOUT
    name = type(exc).__name__.lower()
    text = f"{name} {exc}".lower()
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)

    if status == 429 or "ratelimit" in name or "rate limit" in text or "429" in text:
        return ErrorCode.LLM_RATE_LIMITED
    if status in (401, 403) or "auth" in name or "permissiondenied" in name:
        return ErrorCode.LLM_AUTH_ERROR
    if "safety" in text or "blocked" in text or "content_filter" in text:
        return ErrorCode.LLM_CONTENT_BLOCKED
    if "timeout" in name or "timeout" in text:
        return ErrorCode.LLM_TIMEOUT
    if isinstance(status, int) and 500 <= status < 600:
        return ErrorCode.LLM_UNAVAILABLE
    return ErrorCode.LLM_UNAVAILABLE


# --- Envelope --------------------------------------------------------------


def _now_iso() -> str:
    # Khop chinh xac dinh dang trong CODING_STANDARDS.md: "2026-09-17T10:54:18Z"
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _meta(
    request_id: str,
    started_at: float,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    # time.monotonic() chu khong phai wall-clock: mot buoc nhay NTP giua buoi
    # demo se cho ra latency am neu dung datetime.
    meta: dict[str, Any] = {
        "timestamp": _now_iso(),
        "request_id": request_id,
        "latency_ms": int(round((time.monotonic() - started_at) * 1000)),
    }
    if extra:
        meta.update(extra)
    return meta


def success_envelope(
    data: Mapping[str, Any],
    *,
    request_id: str,
    started_at: float,
    degraded: bool = False,
    degraded_reason: str | None = None,
    extra_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {"degraded": degraded}
    if degraded_reason:
        extra["degraded_reason"] = degraded_reason
    if extra_meta:
        extra.update(extra_meta)
    return {
        "success": True,
        "data": dict(data),
        "error": None,
        "meta": _meta(request_id, started_at, extra),
    }


def error_envelope(
    code: ErrorCode,
    *,
    request_id: str,
    started_at: float,
    details: str | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code.value,
            "message": message_for(code),
            "details": redact(details or "")[:_MAX_DETAILS_CHARS],
        },
        "meta": _meta(request_id, started_at),
    }


# --- Sửa JSON bằng code (tier T1.5a, miễn phí) -----------------------------

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def repair_json_text(raw: str) -> str:
    """Gỡ các lỗi định dạng thường gặp mà không tốn một token nào.

    Luôn chạy trước khi nghĩ tới việc gọi LLM sửa hộ: nó miễn phí, tức thời, và
    xử lý được phần lớn trường hợp thực tế (bọc dấu ```, có lời dẫn, dấu phẩy
    thừa).
    """
    if not raw:
        return ""
    text = raw.strip()

    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()

    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                text = text[start : index + 1]
                break
    else:
        text = text[start:]

    return _TRAILING_COMMA_RE.sub(r"\1", text)


def _parse(raw: str, model: type[BaseModel]) -> tuple[BaseModel | None, str]:
    cleaned = repair_json_text(raw)
    if not cleaned:
        return None, "output rong"
    try:
        return model.model_validate_json(cleaned), ""
    except ValidationError as exc:
        return None, f"schema khong khop: {exc.error_count()} loi"
    except (ValueError, TypeError) as exc:
        return None, f"khong parse duoc JSON: {type(exc).__name__}"


# --- Tier T3/T4: trả lời không cần LLM -------------------------------------


def _extractive_answer(
    chunks: Sequence[RetrievedChunk],
) -> tuple[str, list[Citation]]:
    top = max(chunks, key=lambda c: c.score)
    excerpt = top.text.strip()[:EXTRACTIVE_FALLBACK_EXCERPT_CHARS].strip()
    answer = EXTRACTIVE_FALLBACK_TEMPLATE.format(
        excerpt=excerpt, title=top.title, locator=top.locator()
    )
    citation = Citation(
        source_id=top.source_id,
        title=top.title,
        excerpt=excerpt,
        confidence=0.5,
    )
    return answer, [citation]


def _degraded_envelope(
    code: ErrorCode,
    chunks: Sequence[RetrievedChunk],
    *,
    request_id: str,
    started_at: float,
    tier: str,
    extra_data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if chunks:
        answer, citations = _extractive_answer(chunks)
    else:
        answer, citations = message_for(code), []
    data: dict[str, Any] = {
        "answer": answer,
        "citations": [c.model_dump() for c in citations],
    }
    if extra_data:
        data.update(extra_data)
    return success_envelope(
        data,
        request_id=request_id,
        started_at=started_at,
        degraded=True,
        degraded_reason=code.value,
        extra_meta={"tier": tier},
    )


# --- Fallback ladder -------------------------------------------------------


@dataclass(slots=True)
class _Attempt:
    parsed: BaseModel | None = None
    raw: str = ""
    code: ErrorCode | None = None
    provider: Provider | None = None
    tier: str = ""
    violations: tuple[str, ...] = ()


async def _call_once(
    bundle: PromptBundle,
    *,
    call_llm: LlmCaller,
    provider: Provider,
    budget_s: float,
    deadline_at: float,
) -> tuple[str, ErrorCode | None]:
    remaining = deadline_at - time.monotonic()
    timeout_s = min(budget_s, remaining)
    if timeout_s < _MIN_BUDGET_TO_TRY_S:
        return "", ErrorCode.LLM_TIMEOUT
    try:
        raw = await asyncio.wait_for(
            call_llm(bundle, provider=provider, timeout_s=timeout_s),
            timeout=timeout_s,
        )
        return raw, None
    except Exception as exc:  # noqa: BLE001 - phan loai roi ha cap, khong sap
        return "", _classify(exc)


async def _generate(
    bundle: PromptBundle,
    *,
    call_llm: LlmCaller,
    providers: Sequence[Provider],
    deadline_at: float,
) -> _Attempt:
    """Chạy T0 -> T1 -> T1.5 -> T2 và trả về kết quả parse được đầu tiên."""
    primary = providers[0] if providers else "gemini"
    secondary = providers[1] if len(providers) > 1 else None
    last_code: ErrorCode | None = None
    last_raw = ""
    last_violation = ""

    plan: list[tuple[str, Provider, float]] = [
        ("T0", primary, _TIER_BUDGET_S["T0"]),
        ("T1", primary, _TIER_BUDGET_S["T1"]),
    ]
    if secondary:
        plan.append(("T2", secondary, _TIER_BUDGET_S["T2"]))

    for tier, provider, budget in plan:
        if tier == "T1":
            # Khong bao gio retry loi khong the phuc hoi: dot deadline cho mot
            # lan fail chac chan.
            if last_code and not ERROR_CATALOG[last_code].retryable:
                continue
            await asyncio.sleep(
                min(_RETRY_BACKOFF_S, max(0.0, deadline_at - time.monotonic()))
            )
        if tier == "T2" and last_code == ErrorCode.LLM_CONTENT_BLOCKED:
            continue

        raw, code = await _call_once(
            bundle,
            call_llm=call_llm,
            provider=provider,
            budget_s=budget,
            deadline_at=deadline_at,
        )
        if code is not None:
            last_code = code
            continue

        last_raw = raw
        if guardrails.check_canary(raw, bundle):
            # Khong bao gio tra van ban nay ra ngoai.
            return _Attempt(code=ErrorCode.PROMPT_LEAK_DETECTED, tier=tier)

        parsed, reason = _parse(raw, bundle.response_model)
        if parsed is not None:
            return _Attempt(parsed=parsed, raw=raw, provider=provider, tier=tier)

        last_code = ErrorCode.LLM_INVALID_JSON
        last_violation = reason

        # T1.5b - goi sua dinh dang, chi khi T1.5a (trong _parse) da that bai.
        repair = build_repair_prompt(raw, bundle, [reason] if reason else [])
        repaired, repair_code = await _call_once(
            repair,
            call_llm=call_llm,
            provider=provider,
            budget_s=_TIER_BUDGET_S["T1_5"],
            deadline_at=deadline_at,
        )
        if repair_code is None:
            parsed, reason = _parse(repaired, bundle.response_model)
            if parsed is not None:
                return _Attempt(
                    parsed=parsed, raw=repaired, provider=provider, tier=f"{tier}+T1_5"
                )
            last_violation = reason

    return _Attempt(
        code=last_code or ErrorCode.LLM_UNAVAILABLE,
        raw=last_raw,
        violations=(last_violation,) if last_violation else (),
    )


def _apply_guardrails(
    parsed: BaseModel,
    bundle: PromptBundle,
    rubric: Sequence[RubricCriterion],
) -> tuple[dict[str, Any] | None, guardrails.GuardrailReport]:
    """Chạy guardrail đầu ra tương ứng với task và dựng phần ``data``."""
    if isinstance(parsed, ChatAnswer):
        report = guardrails.check_chat_answer(parsed, bundle)
        if not report.ok:
            return None, report
        return {
            "answer": parsed.answer,
            "citations": [c.model_dump() for c in report.citations],
        }, report

    if isinstance(parsed, TeachBackDiagnosis):
        report = guardrails.check_teach_back(parsed, bundle, rubric=rubric)
        if not report.ok:
            return None, report
        return {
            "answer": parsed.follow_up_question,
            "citations": [
                Citation(
                    source_id=e.source_id,
                    title=bundle.chunk_index[e.source_id].title,
                    excerpt=e.quote,
                    confidence=0.9,
                ).model_dump()
                for e in parsed.evidence
                if e.source_id in bundle.chunk_index
            ],
            "diagnosis": parsed.model_dump(),
        }, report

    if isinstance(parsed, QuizSet):
        cleaned, report = guardrails.check_quiz(parsed, bundle)
        if not report.ok:
            return None, report
        return {
            "answer": "",
            "citations": [],
            "quiz": [item.model_dump(by_alias=True) for item in cleaned.items],
        }, report

    return {"answer": "", "citations": []}, guardrails.GuardrailReport()


async def run_guarded_generation(
    bundle: PromptBundle,
    *,
    call_llm: LlmCaller,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    request_id: str,
    started_at: float,
    providers: Sequence[Provider] = ("gemini", "openai"),
    deadline_s: float = LLM_DEADLINE_S,
    rubric: Sequence[RubricCriterion | Mapping[str, Any]] = (),
    enable_llm_judge: bool = False,
) -> dict[str, Any]:
    """Chạy toàn bộ guardrail + fallback ladder và trả về envelope hoàn chỉnh.

    Đây là hàm duy nhất ``rag_engine.py`` cần gọi sau khi dựng prompt. Nó không
    bao giờ raise: mọi nhánh lỗi đều kết thúc bằng một envelope hợp lệ, nên
    route FastAPI không cần lấy một khối try/except nào.
    """
    items = coerce_chunks(chunks)
    criteria = coerce_rubric(rubric)
    deadline_at = time.monotonic() + deadline_s

    try:
        # G1 + G2 - ket qua da duoc builders ghi san vao bundle.
        if bundle.input_error:
            return error_envelope(
                ErrorCode(bundle.input_error),
                request_id=request_id,
                started_at=started_at,
            )

        # G3 - cong context rong. Tu choi TRUOC khi sinh.
        if bundle.task in ("CHAT", "TEACH_BACK", "QUIZ") and not (
            guardrails.has_retrieval_context(items)
        ):
            return _degraded_envelope(
                ErrorCode.RETRIEVAL_EMPTY,
                [],
                request_id=request_id,
                started_at=started_at,
                tier="T4",
            )

        attempt = await _generate(
            bundle,
            call_llm=call_llm,
            providers=providers,
            deadline_at=deadline_at,
        )

        if attempt.parsed is None:
            code = attempt.code or ErrorCode.INTERNAL_ERROR
            if code == ErrorCode.PROMPT_LEAK_DETECTED:
                return error_envelope(
                    code, request_id=request_id, started_at=started_at
                )
            return _degraded_envelope(
                code,
                items,
                request_id=request_id,
                started_at=started_at,
                tier="T3",
            )

        data, report = _apply_guardrails(attempt.parsed, bundle, criteria)
        if data is None:
            code = ErrorCode(report.error_code or ErrorCode.GUARDRAIL_UNGROUNDED.value)
            return _degraded_envelope(
                code,
                items,
                request_id=request_id,
                started_at=started_at,
                tier="T3",
            )

        extra_meta: dict[str, Any] = {
            "provider": attempt.provider,
            "tier": attempt.tier,
        }
        if bundle.input_flags:
            extra_meta["injection_flags"] = list(bundle.input_flags)
        if report.warnings:
            extra_meta["warnings"] = report.warnings

        # LLM judge - mac dinh ngoai hot path, chi chay khi G6 roi vao vung bat
        # dinh VA con du thoi gian. Judge loi khong bao gio duoc lam hong
        # request cua nguoi dung.
        should_judge = enable_llm_judge or report.needs_judge
        remaining = deadline_at - time.monotonic()
        if should_judge and remaining >= _MIN_BUDGET_FOR_JUDGE_S and data.get("answer"):
            verdict = await _safe_judge(
                str(data["answer"]),
                items,
                call_llm=call_llm,
                provider=attempt.provider or providers[0],
                deadline_at=deadline_at,
            )
            if verdict is not None:
                extra_meta["faithfulness_score"] = verdict.faithfulness_score
                extra_meta["faithfulness_verdict"] = verdict.verdict

        return success_envelope(
            data,
            request_id=request_id,
            started_at=started_at,
            extra_meta=extra_meta,
        )

    except Exception as exc:  # noqa: BLE001 - lop chan cuoi cung, khong duoc sap
        return error_envelope(
            ErrorCode.INTERNAL_ERROR,
            request_id=request_id,
            started_at=started_at,
            details=f"{type(exc).__name__}: {exc}",
        )


async def _safe_judge(
    answer_text: str,
    chunks: Sequence[RetrievedChunk],
    *,
    call_llm: LlmCaller,
    provider: Provider,
    deadline_at: float,
) -> FaithfulnessReport | None:
    bundle = build_faithfulness_prompt(answer_text, chunks)
    raw, code = await _call_once(
        bundle,
        call_llm=call_llm,
        provider=provider,
        budget_s=_JUDGE_BUDGET_S,
        deadline_at=deadline_at,
    )
    if code is not None:
        return None
    parsed, _ = _parse(raw, FaithfulnessReport)
    if not isinstance(parsed, FaithfulnessReport):
        return None
    return guardrails.finalize_faithfulness(parsed)


async def score_faithfulness(
    answer_text: str,
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
    *,
    call_llm: LlmCaller,
    provider: Provider = "gemini",
    request_id: str = "eval",
    timeout_s: float = _JUDGE_BUDGET_S,
) -> FaithfulnessReport:
    """Chấm độ trung thực một câu trả lời — dùng cho ``eval_metrics.py`` (M4).

    Tách khỏi fallback ladder để M4 chạy được với model rẻ hơn và ngân sách thời
    gian riêng, mà không phải chạm vào bất cứ phần nào của luồng production.
    """
    items = coerce_chunks(chunks)
    bundle = build_faithfulness_prompt(answer_text, items, request_id=request_id)
    deadline_at = time.monotonic() + timeout_s
    raw, code = await _call_once(
        bundle,
        call_llm=call_llm,
        provider=provider,
        budget_s=timeout_s,
        deadline_at=deadline_at,
    )
    if code is not None:
        return FaithfulnessReport(claims=[], faithfulness_score=0.0, verdict="FAIL")
    parsed, _ = _parse(raw, FaithfulnessReport)
    if not isinstance(parsed, FaithfulnessReport):
        return FaithfulnessReport(claims=[], faithfulness_score=0.0, verdict="FAIL")
    return guardrails.finalize_faithfulness(parsed)
