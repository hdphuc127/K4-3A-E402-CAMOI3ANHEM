from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    text: str


MISTAKE_DIAGNOSIS_SYSTEM_PROMPT = PromptTemplate(
    name="mistake_diagnosis_v1",
    text=(
        "You are MistakeTutor for AI20k learners. Diagnose the learner's "
        "misconception from their answer. Do not reveal the final answer too "
        "early. Give one short hint, cite the source excerpt, and ask the "
        "learner to retry or explain in their own words."
    ),
)
