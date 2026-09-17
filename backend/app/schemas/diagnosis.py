from typing import Literal

from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    lesson_id: str = Field(default="t06-tokenization", min_length=1)
    question_id: str = Field(default="tokenization-basic-01", min_length=1)
    question_text: str = Field(min_length=1)
    correct_answer: str = Field(min_length=1)
    student_answer: str = Field(min_length=1)
    student_explanation: str | None = None


class SourceCitation(BaseModel):
    source_id: str
    title: str
    excerpt: str
    confidence: float = Field(ge=0, le=1)


class DiagnosisResult(BaseModel):
    question_id: str
    is_correct: bool
    misconception: Literal[
        "answer_is_correct",
        "counting_characters_or_spaces",
        "ambiguous_or_unknown",
    ]
    hint: str
    next_action: Literal[
        "retry_answer",
        "ask_for_reasoning",
        "explain_reasoning",
    ]
    citations: list[SourceCitation]
    debug_prompt_name: str
