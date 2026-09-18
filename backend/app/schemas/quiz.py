from __future__ import annotations

from pydantic import BaseModel, Field


class QuizRequest(BaseModel):
    topic: str = Field(min_length=1)
    weak_points: list[str] = Field(default_factory=list)
    difficulty: str = "MEDIUM"
    num_items: int = 4


class QuizItemOut(BaseModel):
    id: str
    prompt: str
    options: list[str]
    correct: int
    why: str
    topic: str
    source_id: str


class QuizResult(BaseModel):
    quiz_id: str
    difficulty: str
    items: list[QuizItemOut]
