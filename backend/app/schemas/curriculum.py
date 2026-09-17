from pydantic import BaseModel


class LearningModule(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None
    track: str
    created_at: str


class Concept(BaseModel):
    id: int
    module_id: int
    slug: str
    title: str
    expected_summary: str
    common_gap: str | None
    created_at: str


class ConceptList(BaseModel):
    module: LearningModule
    concepts: list[Concept]
