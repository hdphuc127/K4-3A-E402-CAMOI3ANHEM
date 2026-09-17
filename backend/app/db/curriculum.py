import sqlite3
from dataclasses import dataclass

from app.db.session import get_connection


@dataclass(frozen=True)
class LearningModuleRecord:
    id: int
    slug: str
    title: str
    description: str | None
    track: str
    created_at: str


@dataclass(frozen=True)
class ConceptRecord:
    id: int
    module_id: int
    slug: str
    title: str
    expected_summary: str
    common_gap: str | None
    created_at: str


def list_learning_modules() -> list[LearningModuleRecord]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, slug, title, description, track, created_at
            FROM learning_modules
            ORDER BY id ASC
            """
        ).fetchall()
    return [_row_to_module(row) for row in rows]


def get_learning_module(module_id: int) -> LearningModuleRecord | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, slug, title, description, track, created_at
            FROM learning_modules
            WHERE id = ?
            """,
            (module_id,),
        ).fetchone()
    return None if row is None else _row_to_module(row)


def list_concepts_by_module(module_id: int) -> list[ConceptRecord]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, module_id, slug, title, expected_summary, common_gap, created_at
            FROM concepts
            WHERE module_id = ?
            ORDER BY id ASC
            """,
            (module_id,),
        ).fetchall()
    return [_row_to_concept(row) for row in rows]


def _row_to_module(row: sqlite3.Row) -> LearningModuleRecord:
    return LearningModuleRecord(
        id=int(row["id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        description=None if row["description"] is None else str(row["description"]),
        track=str(row["track"]),
        created_at=str(row["created_at"]),
    )


def _row_to_concept(row: sqlite3.Row) -> ConceptRecord:
    return ConceptRecord(
        id=int(row["id"]),
        module_id=int(row["module_id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        expected_summary=str(row["expected_summary"]),
        common_gap=None if row["common_gap"] is None else str(row["common_gap"]),
        created_at=str(row["created_at"]),
    )
