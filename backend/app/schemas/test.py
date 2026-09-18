from __future__ import annotations

from pydantic import BaseModel, Field


class TestRequest(BaseModel):
    week_id: str = Field(min_length=1)


class TestItemOut(BaseModel):
    id: str
    prompt: str
    options: list[str]
    correct: int
    why: str
    misconception: str
    topic: str
    source_id: str


class TestResult(BaseModel):
    test_id: str
    items: list[TestItemOut]
