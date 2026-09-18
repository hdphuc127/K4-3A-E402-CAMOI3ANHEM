"""Mo hinh du lieu cho tang prompt / guardrail / fallback.

Hai nhom mo hinh, rang buoc hoan toan khac nhau:

1. Mo hinh DAU VAO (``RetrievedChunk``, ``RubricCriterion``): chi dung trong
   Python, khong bao gio bi chuyen thanh JSON Schema gui cho LLM. Duoc phep
   dung ``| None``, gia tri mac dinh, union.

2. Mo hinh DAU RA CUA LLM (``ChatAnswer``, ``TeachBackDiagnosis``, ``QuizSet``,
   ``FaithfulnessReport``): bi ep qua ``response_schema`` cua Gemini - von chi
   nhan mot tap con cua OpenAPI. Rang buoc bat buoc:

       - moi field deu required, khong ``Optional``, khong ``Union``
       - khong ``dict[str, X]``
       - enum viet bang ``Literal[...]`` voi gia tri ASCII UPPER_SNAKE
       - vang mat bieu dien bang sentinel ``""`` / ``[]``, khong phai ``null``

   Vi pham cac rang buoc nay se lam Gemini tra 400 dung luc demo. Test
   ``test_gemini_schema_has_no_unsupported_keys`` chan viec do.

Nguyen tac thu hai, quan trong khong kem: **field nao code suy ra duoc thi model
khong duoc sinh ra**. Vi du ``Citation.title`` duoc tra cuu tu chunk goc chu
khong phai do LLM viet - xoa han mot lop hallucination ma khong ton gi.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Provider = Literal["gemini", "openai"]
TaskName = Literal["CHAT", "TEACH_BACK", "QUIZ", "JUDGE"]


# ---------------------------------------------------------------------------
# 1. Mo hinh dau vao
# ---------------------------------------------------------------------------


class RetrievedChunk(BaseModel):
    """Mot doan tai lieu do rag_engine.py tra ve.

    ``source_id`` la khoa noi ca he thong: guardrail G5 doi chieu moi trich dan
    voi tap source_id that su duoc dua vao prompt. Vi vay dinh dang phai ON DINH
    qua moi lan re-index, khong duoc dung chi so trong list.

    Dinh dang da chot::

        {pack}-{week}-{kind}-{lesson}#{chunk_no}
        vd: "vlearn-w2-transcript-lab1#c12"
    """

    model_config = ConfigDict(extra="ignore")

    source_id: str
    title: str
    text: str
    kind: Literal["transcript", "slide", "note"] = "transcript"
    slide_page: int | None = None
    timestamp: str | None = None
    lesson_id: str | None = None
    score: float = 0.0

    def locator(self) -> str:
        """Chuoi dinh vi nguon, do CODE sinh ra chu khong phai LLM.

        Chuoi nay di thang vao prompt VA vao cau tra loi hien cho hoc vien o
        tier T3, nen phai viet tieng Viet co dau.
        """
        if self.slide_page is not None:
            return f"slide {self.slide_page}"
        if self.timestamp:
            return f"phút {self.timestamp}"
        return "transcript"


class RubricCriterion(BaseModel):
    """Mot tieu chi cham loi giai thich cua hoc vien trong luong teach-back."""

    model_config = ConfigDict(extra="ignore")

    rubric_id: str
    description: str
    weight: float = 1.0


def coerce_chunks(
    chunks: Sequence[RetrievedChunk | Mapping[str, Any]],
) -> list[RetrievedChunk]:
    """Nhan ca ``RetrievedChunk`` lan dict tho tu Qdrant.

    Nho ham nay, rag_engine.py khong bi ep import type cua tang prompt - hai
    nguoi build song song duoc ma khong cham vao file cua nhau.
    """
    return [
        c if isinstance(c, RetrievedChunk) else RetrievedChunk.model_validate(dict(c))
        for c in chunks
    ]


def coerce_rubric(
    rubric: Sequence[RubricCriterion | Mapping[str, Any]],
) -> list[RubricCriterion]:
    return [
        r if isinstance(r, RubricCriterion) else RubricCriterion.model_validate(dict(r))
        for r in rubric
    ]


# ---------------------------------------------------------------------------
# 2a. Dau ra LLM - luong chat RAG
# ---------------------------------------------------------------------------


class CitationDraft(BaseModel):
    """Trich dan do MODEL sinh ra. Chua co ``title`` - code se tra cuu sau."""

    model_config = ConfigDict(extra="ignore")

    source_id: str = Field(description="Sao chep nguyen van tu thuoc tinh source_id")
    excerpt: str = Field(description="NGUYEN VAN tu <content> cua dung tai lieu do")
    confidence: float = Field(description="0.0 den 1.0")


class ChatAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str
    citations: list[CitationDraft]
    answerable: bool
    injection_detected: bool
    general_knowledge_used: bool = Field(
        description=(
            "True khi answerable=false nhung cau tra loi dung kien thuc chung "
            "ve AI/LLM de mo rong ngoai retrieved_documents, thay vi tu choi."
        )
    )


class Citation(BaseModel):
    """Trich dan trong envelope tra ve client.

    Dung dinh dang ``CODING_STANDARDS.md`` muc 3: source_id / title / excerpt /
    confidence. ``title`` do code dien tu chunk goc.
    """

    source_id: str
    title: str
    excerpt: str
    confidence: float


# ---------------------------------------------------------------------------
# 2b. Dau ra LLM - luong teach-back (lat cat CP1)
# ---------------------------------------------------------------------------


class Evidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_id: str
    quote: str = Field(description="Nguyen van tu transcript")
    rubric_id: str = Field(description='De "" khi bang chung chi den tu transcript')


class TeachBackDiagnosis(BaseModel):
    """Ket qua chan doan lo hong kien thuc.

    CHU Y - day la diem quan trong nhat cua ca thiet ke:

    ``verdict`` KHONG co gia tri ``UNDERSTOOD``. Muc automation cua san pham la
    "conditional augmentation" (checkpoint-1-track-d-draft.md muc 7): AI khong
    duoc tu ket luan hoc vien "da hieu", vi chan doan sai se khien hoc vien mang
    cach hieu sai sang chuong sau.

    Cam bang lieu do manh hon cam bang van xuoi: structured output ep model chi
    duoc chon trong ba gia tri duoi day, nen model KHONG THE phat ngon ket luan
    do - khong phu thuoc vao viec no co chiu nghe loi hay khong.

    Chi co phep so khop trac nghiem deterministic moi duoc lat trang thai mot
    chu de sang "da on & xac nhan".
    """

    model_config = ConfigDict(extra="ignore")

    verdict: Literal["GAP_FOUND", "NEEDS_MORE_EVIDENCE", "OFF_TOPIC"]
    gap_title: str
    gap_explanation: str
    evidence: list[Evidence]
    follow_up_question: str
    covered_points: list[str] = Field(
        description="Mo ta su viec ('da neu duoc y X'), khong danh gia ('da hieu X')"
    )


# ---------------------------------------------------------------------------
# 2c. Dau ra LLM - luong sinh quiz
# ---------------------------------------------------------------------------


class QuizItem(BaseModel):
    """Mot cau trac nghiem.

    Alias camelCase de ``model_dump(by_alias=True)`` ra dung shape ma UI dang
    doc: ``{prompt, options, correct, whyCorrect, whyWrong}``.
    Xem ``tests/fixtures/prompts_quiz_ui_shape.json``.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )

    prompt: str
    options: list[str]
    correct: int = Field(description="Chi so 0-based cua dap an dung")
    why_correct: str
    why_wrong: str
    source_id: str = Field(description="Chunk ma cau hoi nay duoc rut ra")


class QuizSet(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[QuizItem]


# ---------------------------------------------------------------------------
# 2d. Dau ra LLM - judge do trung thuc
# ---------------------------------------------------------------------------


class ClaimVerdict(BaseModel):
    model_config = ConfigDict(extra="ignore")

    claim: str
    verdict: Literal[
        "SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "CONTRADICTED"
    ]
    supporting_source_id: str = Field(description='De "" khi khong tim thay cu')
    supporting_quote: str = Field(description='De "" khi khong tim thay cu')


class FaithfulnessReport(BaseModel):
    """Bao cao do trung thuc.

    ``faithfulness_score`` va ``verdict`` duoc GHI DE bang Python sau khi parse.
    Model chi lam viec no gioi - gan nhan tung claim; con phep tinh diem thi
    code lam, vi model tinh toan kem va khong on dinh.
    """

    model_config = ConfigDict(extra="ignore")

    claims: list[ClaimVerdict]
    faithfulness_score: float = 0.0
    verdict: Literal["PASS", "WARN", "FAIL"] = "FAIL"


# ---------------------------------------------------------------------------
# 3. PromptBundle + giao dien goi LLM
# ---------------------------------------------------------------------------


@runtime_checkable
class LlmCaller(Protocol):
    """Giao dien goi LLM do rag_engine.py / backend cung cap.

    Tang prompt KHONG import bat ky SDK nao cua LLM. Nho vay toan bo test cua
    tang nay chay duoc trong mot venv chi co pydantic + pytest, khi chua ai co
    API key.

    Ham phai tra ve chuoi text/JSON tho tu provider, va nem exception khi loi
    transport (timeout, 429, 5xx, ...).
    """

    async def __call__(
        self,
        bundle: PromptBundle,
        *,
        provider: Provider,
        timeout_s: float,
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class PromptBundle:
    """Mot prompt da dung xong, trung lap ve provider.

    ``allowed_source_ids`` va ``chunk_index`` la thu nuoi guardrail G5/G6: sau
    khi model tra loi, code doi chieu moi source_id va moi excerpt voi dung tap
    du lieu da dua vao prompt nay.
    """

    system: str
    user: str
    response_model: type[BaseModel]
    temperature: float
    max_output_tokens: int
    allowed_source_ids: tuple[str, ...]
    chunk_index: Mapping[str, RetrievedChunk]
    canary: str
    task: TaskName

    # Ket qua kiem tra dau vao (guardrail G1/G2), do builders ghi vao.
    # ``input_error`` mang gia tri cua ErrorCode duoi dang chuoi, hoac "" khi
    # dau vao hop le. Luu chuoi thay vi enum de schemas.py khong phai import
    # fallback.py - neu khong se thanh vong lap import.
    #
    # Nho hai truong nay, run_guarded_generation tu tra ve envelope loi dung
    # chuan ma rag_engine.py khong can viet lay mot khoi try/except nao.
    input_error: str = ""
    input_flags: tuple[str, ...] = ()
    input_severity: int = 0

    def as_openai_messages(self) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user},
        ]

    def as_openai_response_format(self) -> dict[str, Any]:
        # Import trong than ham de tranh vong lap schemas <-> schema_compat.
        from app.core.prompts.schema_compat import to_openai_response_format

        return to_openai_response_format(self.response_model)

    def as_gemini_args(self) -> dict[str, Any]:
        from app.core.prompts.schema_compat import to_gemini_schema

        return {
            "system_instruction": self.system,
            "contents": [{"role": "user", "parts": [{"text": self.user}]}],
            "generation_config": {
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "response_mime_type": "application/json",
                "response_schema": to_gemini_schema(self.response_model),
            },
        }

    def as_single_turn(self) -> str:
        """Cho provider khong co system role - ghep hai turn lam mot.

        Compose duoc ma khong phai viet lai gi, vi ca prompt von da la XML.
        """
        return (
            "<system_instructions>\n"
            f"{self.system}\n"
            "</system_instructions>\n\n"
            f"{self.user}"
        )
