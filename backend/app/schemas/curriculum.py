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


class Topic(BaseModel):
    id: str
    name: str
    summary: str


class Week(BaseModel):
    id: str
    title: str
    subtitle: str
    period: str
    topics: list[str]
    available: bool


class Question(BaseModel):
    id: str
    topic: str
    prompt: str
    options: list[str]
    correct: int
    why: str
    misconception: str


class LessonSlide(BaseModel):
    title: str
    body: list[str]
    note: str | None = None


class Lesson(BaseModel):
    lesson: str
    slides: list[LessonSlide]


class CheckQuestion(BaseModel):
    prompt: str
    options: list[str]
    correct: int
    whyCorrect: str
    whyWrong: str


class ReviewData(BaseModel):
    topics: dict[str, Topic]
    weeks: list[Week]
    questions: list[Question]
    lessons: dict[str, Lesson]
    check_questions: dict[str, list[CheckQuestion]]
