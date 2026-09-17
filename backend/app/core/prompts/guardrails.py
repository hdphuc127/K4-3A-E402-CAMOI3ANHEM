"""Guardrail G1-G12.

Toàn bộ kiểm tra trong file này là Python thuần: không network, không token,
dưới một mili-giây, test được khi chưa ai có API key.

Chỉ một loại việc thực sự cần tới LLM — suy luận ngữ nghĩa ("đoạn transcript này
có *thực sự* chứng minh khẳng định kia không"). Việc đó nằm ở
``faithfulness.py`` phía người gọi, mặc định TẮT trên hot path và chỉ bật khi
G6 rơi vào vùng bất định.

Nguyên tắc vận hành: **guardrail lỗi thì hạ cấp, không đánh sập**. Một guardrail
có thể làm hỏng request của người dùng là bug tệ hơn thứ nó canh.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.core.prompts.schemas import (
    ChatAnswer,
    Citation,
    FaithfulnessReport,
    PromptBundle,
    QuizItem,
    QuizSet,
    RetrievedChunk,
    RubricCriterion,
    TeachBackDiagnosis,
)
from app.core.prompts.templates.quiz_gen import (
    BANNED_OPTION_PATTERNS,
    QUIZ_OPTIONS_PER_ITEM,
)
from app.core.prompts.templates.teach_back import FORBIDDEN_PHRASE_PATTERNS

__all__ = [
    "GuardrailReport",
    "MIN_RETRIEVAL_SCORE",
    "EXCERPT_MATCH_STRICT",
    "EXCERPT_MATCH_UNCERTAIN",
    "normalize",
    "excerpt_containment",
    "has_retrieval_context",
    "check_canary",
    "hydrate_citations",
    "check_chat_answer",
    "check_teach_back",
    "check_quiz",
    "finalize_faithfulness",
    "is_mostly_vietnamese",
]

MIN_RETRIEVAL_SCORE = 0.35

# G6: ngưỡng độ chứa token của excerpt so với chunk gốc.
EXCERPT_MATCH_STRICT = 0.85
EXCERPT_MATCH_UNCERTAIN = 0.50

MIN_QUIZ_ITEMS = 3
MAX_QUIZ_ITEMS = 5
MAX_CITATIONS = 3

_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_PUNCT_STRIP = " \t\n\r.,;:!?\"'()[]{}<>-–—…"

_FORBIDDEN_RE = re.compile("|".join(FORBIDDEN_PHRASE_PATTERNS))
_BANNED_OPTION_RE = re.compile("|".join(BANNED_OPTION_PATTERNS))

# G12: chữ cái chỉ có trong tiếng Việt, dùng để ước lượng ngôn ngữ đầu ra.
_VIET_CHARS = set("ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ")


@dataclass(slots=True)
class GuardrailReport:
    """Kết quả chạy guardrail trên một output đã parse.

    ``ok=False`` nghĩa là output không dùng được nguyên trạng. Tầng
    orchestration quyết định sửa (T1.5b) hay hạ cấp (T3/T4) — guardrail không
    tự ý kết thúc request.
    """

    ok: bool = True
    error_code: str = ""
    violations: list[str] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    needs_judge: bool = False
    warnings: list[str] = field(default_factory=list)

    def fail(self, code: str, message: str) -> GuardrailReport:
        self.ok = False
        if not self.error_code:
            self.error_code = code
        self.violations.append(message)
        return self


def normalize(text: str) -> str:
    """Chuẩn hoá để so khớp: NFKC, casefold, gộp khoảng trắng, bỏ dấu câu biên."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return _WS_RE.sub(" ", folded).strip(_PUNCT_STRIP)


def excerpt_containment(excerpt: str, source_text: str) -> float:
    """Mức độ excerpt thực sự nằm trong chunk gốc, trong khoảng 0.0-1.0.

    Khớp nguyên văn trả về 1.0. Nếu không, dùng độ chứa token để dung thứ việc
    model bỏ một dấu phẩy hoặc sửa một lỗi nhận dạng giọng nói — nhưng vẫn phát
    hiện được trích dẫn hoàn toàn bịa ra.
    """
    norm_excerpt = normalize(excerpt)
    norm_source = normalize(source_text)
    if not norm_excerpt:
        return 0.0
    if norm_excerpt in norm_source:
        return 1.0

    tokens = _TOKEN_RE.findall(norm_excerpt)
    if not tokens:
        return 0.0
    source_tokens = set(_TOKEN_RE.findall(norm_source))
    hit = sum(1 for t in tokens if t in source_tokens)
    return hit / len(tokens)


def has_retrieval_context(
    chunks: Sequence[RetrievedChunk],
    *,
    min_score: float = MIN_RETRIEVAL_SCORE,
) -> bool:
    """G3 — cổng context rỗng.

    Guardrail đòn bẩy cao nhất của cả hệ thống. Phần lớn hallucination xảy ra
    đúng lúc retrieval không trả về gì hữu ích và model lịch sự lấp chỗ trống.
    Từ chối TRƯỚC khi sinh triệt tiêu nguyên lớp lỗi đó, tiết kiệm một lượt gọi
    API và vài giây deadline, chi phí bằng không.
    """
    if not chunks:
        return False
    return max(c.score for c in chunks) >= min_score


def check_canary(raw_output: str, bundle: PromptBundle) -> bool:
    """G8 — phát hiện rò rỉ system prompt. True nghĩa là ĐÃ rò rỉ."""
    return bool(bundle.canary) and bundle.canary in raw_output


def is_mostly_vietnamese(text: str) -> bool:
    """G12 — chỉ cảnh báo, không bao giờ chặn."""
    if not text.strip():
        return False
    lowered = unicodedata.normalize("NFC", text).casefold()
    return any(ch in _VIET_CHARS for ch in lowered)


def hydrate_citations(
    drafts: Sequence[object],
    bundle: PromptBundle,
    report: GuardrailReport,
) -> list[Citation]:
    """G5 + G6 — lọc trích dẫn và điền ``title`` từ chunk gốc.

    ``title`` do CODE tra cứu chứ không do model sinh: field nào code suy ra
    được thì model không được sinh ra.
    """
    kept: list[Citation] = []
    for draft in drafts[:MAX_CITATIONS]:
        source_id = getattr(draft, "source_id", "")
        excerpt = getattr(draft, "excerpt", "")
        confidence = float(getattr(draft, "confidence", 0.0) or 0.0)

        chunk = bundle.chunk_index.get(source_id)
        if chunk is None:
            report.violations.append(f"source_id khong co that: {source_id!r}")
            continue

        ratio = excerpt_containment(excerpt, chunk.text)
        if ratio < EXCERPT_MATCH_UNCERTAIN:
            report.violations.append(f"excerpt khong co trong chunk {source_id!r}")
            continue
        if ratio < EXCERPT_MATCH_STRICT:
            confidence = min(confidence, 0.5)
            report.needs_judge = True

        kept.append(
            Citation(
                source_id=source_id,
                title=chunk.title,
                excerpt=excerpt,
                confidence=max(0.0, min(1.0, confidence)),
            )
        )
    return kept


def check_chat_answer(answer: ChatAnswer, bundle: PromptBundle) -> GuardrailReport:
    """G5, G6, G7 và G12 cho luồng chat."""
    report = GuardrailReport()

    if not answer.answer.strip():
        return report.fail("SCHEMA_VALIDATION_FAILED", "answer rong")

    report.citations = hydrate_citations(answer.citations, bundle, report)

    if answer.answerable and not report.citations:
        if answer.citations:
            # Model co trich dan nhung khong cai nao tru duoc -> bia nguon.
            return report.fail(
                "GUARDRAIL_UNGROUNDED", "moi trich dan deu khong doi chieu duoc"
            )
        return report.fail("GUARDRAIL_NO_CITATION", "cau tra loi khong co trich dan")

    if not is_mostly_vietnamese(answer.answer):
        report.warnings.append("cau tra loi co the khong phai tieng Viet")

    return report


def check_teach_back(
    diagnosis: TeachBackDiagnosis,
    bundle: PromptBundle,
    *,
    rubric: Sequence[RubricCriterion] = (),
) -> GuardrailReport:
    """G9 + G10 — tầng thứ hai của luật "không kết luận học viên đã hiểu".

    Tầng thứ nhất nằm trong lược đồ: ``TeachBackDiagnosis.verdict`` không có giá
    trị ``UNDERSTOOD`` nên model không thể phát ngôn kết luận đó.

    Tầng thứ ba, và là guarantee thật, nằm ngoài backend: chỉ phép so khớp trắc
    nghiệm deterministic ở frontend mới được lật trạng thái một chủ đề sang "đã
    ôn & xác nhận". Không có đường nào cho LLM chạm vào trạng thái đó.
    """
    report = GuardrailReport()

    texts = [
        diagnosis.gap_title,
        diagnosis.gap_explanation,
        diagnosis.follow_up_question,
        *diagnosis.covered_points,
    ]
    for text in texts:
        match = _FORBIDDEN_RE.search(normalize(text))
        if match:
            report.fail(
                "GUARDRAIL_FORBIDDEN_CLAIM",
                f"cum tu bi cam: {match.group(0)!r}",
            )
            break

    if not diagnosis.evidence:
        report.fail("GUARDRAIL_UNGROUNDED", "chan doan khong co evidence")

    rubric_ids = {r.rubric_id for r in rubric}
    for item in diagnosis.evidence:
        chunk = bundle.chunk_index.get(item.source_id)
        if chunk is None:
            report.fail(
                "GUARDRAIL_UNGROUNDED",
                f"evidence tro toi source_id khong co that: {item.source_id!r}",
            )
            continue
        if excerpt_containment(item.quote, chunk.text) < EXCERPT_MATCH_UNCERTAIN:
            report.fail(
                "GUARDRAIL_UNGROUNDED",
                f"quote khong co trong chunk {item.source_id!r}",
            )
        if item.rubric_id and rubric_ids and item.rubric_id not in rubric_ids:
            report.fail(
                "GUARDRAIL_UNGROUNDED",
                f"rubric_id khong co that: {item.rubric_id!r}",
            )

    if diagnosis.follow_up_question.count("?") != 1:
        report.warnings.append("follow_up_question nen la dung mot cau hoi")

    return report


def _option_is_banned(option: str) -> bool:
    return bool(_BANNED_OPTION_RE.search(normalize(option)))


def _quiz_item_is_valid(item: QuizItem, bundle: PromptBundle) -> str:
    """Trả về lý do loại bỏ, hoặc chuỗi rỗng khi câu hỏi hợp lệ."""
    if len(item.options) != QUIZ_OPTIONS_PER_ITEM:
        return f"can dung {QUIZ_OPTIONS_PER_ITEM} phuong an"
    if not 0 <= item.correct < QUIZ_OPTIONS_PER_ITEM:
        return f"chi so dap an ngoai khoang: {item.correct}"
    if len({normalize(o) for o in item.options}) != QUIZ_OPTIONS_PER_ITEM:
        return "co phuong an trung nhau"
    if any(_option_is_banned(o) for o in item.options):
        return "chua phuong an bi cam"
    if not item.prompt.strip():
        return "than cau hoi rong"
    if not item.why_correct.strip() or not item.why_wrong.strip():
        return "thieu phan giai thich"
    if item.source_id not in bundle.chunk_index:
        return f"source_id khong co that: {item.source_id!r}"
    return ""


def check_quiz(quiz: QuizSet, bundle: PromptBundle) -> tuple[QuizSet, GuardrailReport]:
    """G11 — kiểm tra cấu trúc bộ trắc nghiệm.

    Loại bỏ từng câu hỏng thay vì vứt cả bộ: ba câu tốt vẫn dùng được, còn một
    câu hỏng thì làm sai lệch việc đánh giá học viên.
    """
    report = GuardrailReport()
    kept: list[QuizItem] = []

    for index, item in enumerate(quiz.items):
        reason = _quiz_item_is_valid(item, bundle)
        if reason:
            report.violations.append(f"cau {index + 1}: {reason}")
            continue
        kept.append(item)

    kept = kept[:MAX_QUIZ_ITEMS]

    if len(kept) < MIN_QUIZ_ITEMS:
        report.fail(
            "GUARDRAIL_QUIZ_INVALID",
            f"chi con {len(kept)} cau hop le, can toi thieu {MIN_QUIZ_ITEMS}",
        )
        return QuizSet(items=kept), report

    if len({item.correct for item in kept}) == 1 and len(kept) > 1:
        report.warnings.append("moi cau deu co dap an dung o cung mot vi tri")

    return QuizSet(items=kept), report


def finalize_faithfulness(report: FaithfulnessReport) -> FaithfulnessReport:
    """Tính lại điểm bằng code — model chỉ gán nhãn từng claim.

    Model gán nhãn tốt nhưng tính toán kém và không ổn định, nên phép cộng do
    Python làm. Hàm này cũng chính là thứ ``tests/eval_metrics.py`` (M4) dùng để
    đo Accuracy cho DoD 80%.
    """
    if not report.claims:
        return FaithfulnessReport(claims=[], faithfulness_score=0.0, verdict="FAIL")

    weights = {"SUPPORTED": 1.0, "PARTIALLY_SUPPORTED": 0.5}
    total = sum(weights.get(c.verdict, 0.0) for c in report.claims)
    score = total / len(report.claims)

    has_contradiction = any(c.verdict == "CONTRADICTED" for c in report.claims)
    if has_contradiction or score < 0.6:
        verdict = "FAIL"
    elif score < 0.8:
        verdict = "WARN"
    else:
        verdict = "PASS"

    return FaithfulnessReport(
        claims=report.claims,
        faithfulness_score=round(score, 4),
        verdict=verdict,
    )
