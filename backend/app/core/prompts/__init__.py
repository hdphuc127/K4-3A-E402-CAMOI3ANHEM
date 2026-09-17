"""Prompt / guardrail / fallback layer.

Re-exports the public surface of the submodules so callers can do
``from app.core.prompts import build_chat_prompt`` instead of reaching into
``builders`` / ``fallback`` / ``schema_compat`` directly.
"""

from __future__ import annotations

from app.core.prompts.builders import (
    MAX_EXPLANATION_CHARS,
    MAX_QUESTION_CHARS,
    build_chat_prompt,
    build_faithfulness_prompt,
    build_quiz_prompt,
    build_repair_prompt,
    build_teach_back_prompt,
)
from app.core.prompts.fallback import (
    ERROR_CATALOG,
    LLM_DEADLINE_S,
    ErrorCode,
    ErrorSpec,
    error_envelope,
    redact,
    repair_json_text,
    run_guarded_generation,
    score_faithfulness,
    success_envelope,
)
from app.core.prompts.schema_compat import (
    UnsupportedSchemaError,
    to_gemini_schema,
    to_openai_response_format,
)
from app.core.prompts.schemas import (
    ChatAnswer,
    FaithfulnessReport,
    QuizSet,
    TeachBackDiagnosis,
)

__all__ = [
    "MAX_EXPLANATION_CHARS",
    "MAX_QUESTION_CHARS",
    "build_chat_prompt",
    "build_faithfulness_prompt",
    "build_quiz_prompt",
    "build_repair_prompt",
    "build_teach_back_prompt",
    "ERROR_CATALOG",
    "LLM_DEADLINE_S",
    "ErrorCode",
    "ErrorSpec",
    "error_envelope",
    "redact",
    "repair_json_text",
    "run_guarded_generation",
    "score_faithfulness",
    "success_envelope",
    "UnsupportedSchemaError",
    "to_gemini_schema",
    "to_openai_response_format",
    "ChatAnswer",
    "FaithfulnessReport",
    "QuizSet",
    "TeachBackDiagnosis",
]
