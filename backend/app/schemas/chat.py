from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.diagnosis import SourceCitation


class ChatContext(BaseModel):
    label: str = ""
    topic: str | None = None


class ChatTurn(BaseModel):
    role: Literal["user", "ai"]
    text: str = ""


class TutorChatRequest(BaseModel):
    text: str = Field(min_length=1)
    context: ChatContext = Field(default_factory=ChatContext)
    messages: list[ChatTurn] = Field(default_factory=list)


class ChatResult(BaseModel):
    text: str
    citations: list[SourceCitation] = Field(default_factory=list)
