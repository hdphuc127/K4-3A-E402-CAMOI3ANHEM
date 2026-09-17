import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings


def initialize_database() -> None:
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                track TEXT NOT NULL DEFAULT 'D',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                slug TEXT NOT NULL,
                title TEXT NOT NULL,
                expected_summary TEXT NOT NULL,
                common_gap TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (module_id) REFERENCES learning_modules(id),
                UNIQUE (module_id, slug)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS source_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER NOT NULL,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                citation_label TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (concept_id) REFERENCES concepts(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rubric_criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                max_score INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (concept_id) REFERENCES concepts(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS review_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_progress',
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (module_id) REFERENCES learning_modules(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS teachback_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                concept_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                student_explanation TEXT NOT NULL,
                attempt_no INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES review_sessions(id),
                FOREIGN KEY (concept_id) REFERENCES concepts(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS gap_diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                gap_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                feedback TEXT NOT NULL,
                followup_question TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0,
                source_chunk_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attempt_id) REFERENCES teachback_attempts(id),
                FOREIGN KEY (source_chunk_id) REFERENCES source_chunks(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_research_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                respondent_label TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                normalized_answer TEXT,
                evidence_note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS willing_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                class_room TEXT,
                commitment_note TEXT NOT NULL,
                planned_test_time TEXT,
                status TEXT NOT NULL DEFAULT 'planned',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        seed_default_learning_content(connection)
        connection.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def seed_default_learning_content(connection: sqlite3.Connection) -> None:
    module_id = _ensure_learning_module(connection)
    concept_id = _ensure_concept(connection, module_id)
    source_chunk_id = _ensure_source_chunk(connection, concept_id)
    _ensure_rubric(connection, concept_id)

    _ = source_chunk_id


def _ensure_learning_module(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT id FROM learning_modules WHERE slug = ?",
        ("llm-review",),
    ).fetchone()
    if row is not None:
        return int(row["id"])
    cursor = connection.execute(
        """
        INSERT INTO learning_modules (slug, title, description, track)
        VALUES (?, ?, ?, ?)
        """,
        (
            "llm-review",
            "Review chuong LLM",
            "Phien teach-back giup hoc vien phat hien lo hong kien thuc sau khi hoc chuong LLM.",
            "D",
        ),
    )
    return int(cursor.lastrowid)


def _ensure_concept(connection: sqlite3.Connection, module_id: int) -> int:
    row = connection.execute(
        "SELECT id FROM concepts WHERE module_id = ? AND slug = ?",
        (module_id, "why-llm-hallucinates"),
    ).fetchone()
    if row is not None:
        return int(row["id"])
    cursor = connection.execute(
        """
        INSERT INTO concepts (
            module_id, slug, title, expected_summary, common_gap
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            module_id,
            "why-llm-hallucinates",
            "Vi sao LLM co the bia",
            "Hoc vien can giai thich duoc LLM du doan token dua tren mau da hoc, nen co the tao cau nghe hop ly nhung sai neu thieu nguon can cu hoac truy hoi sai ngu canh.",
            "Chi noi 'AI chua du thong minh' ma khong neu co che du doan token va gioi han nguon can cu.",
        ),
    )
    return int(cursor.lastrowid)


def _ensure_source_chunk(connection: sqlite3.Connection, concept_id: int) -> int:
    row = connection.execute(
        "SELECT id FROM source_chunks WHERE source_id = ?",
        ("llm-hallucination-transcript-01",),
    ).fetchone()
    if row is not None:
        return int(row["id"])
    cursor = connection.execute(
        """
        INSERT INTO source_chunks (
            concept_id, source_id, source_type, title, excerpt, citation_label
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            concept_id,
            "llm-hallucination-transcript-01",
            "transcript",
            "Transcript chuong LLM - Hallucination",
            "LLM sinh cau tra loi bang cach du doan token tiep theo dua tren xac suat va ngu canh. Neu ngu canh thieu, nguon can cu sai, hoac mo hinh khong co co che kiem chung su that, cau tra loi co the nghe hop ly nhung khong dung.",
            "Transcript LLM / Hallucination / doan 01",
        ),
    )
    return int(cursor.lastrowid)


def _ensure_rubric(connection: sqlite3.Connection, concept_id: int) -> None:
    existing = connection.execute(
        "SELECT COUNT(*) AS count FROM rubric_criteria WHERE concept_id = ?",
        (concept_id,),
    ).fetchone()
    if existing is not None and int(existing["count"]) > 0:
        return
    rows = [
        (
            concept_id,
            "Co che du doan token",
            "Co nhac den viec LLM sinh tiep token dua tren mau/xac suat/ngu canh.",
            1,
        ),
        (
            concept_id,
            "Gioi han nguon can cu",
            "Co neu rang cau tra loi co the sai khi thieu nguon, ngu canh khong du, hoac khong truy xuat dung tai lieu.",
            1,
        ),
        (
            concept_id,
            "Phan biet nghe hop ly va dung su that",
            "Co giai thich rang cau nghe thuyet phuc khong dong nghia voi co can cu dung.",
            1,
        ),
    ]
    connection.executemany(
        """
        INSERT INTO rubric_criteria (concept_id, name, description, max_score)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
