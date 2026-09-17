import sqlite3
from dataclasses import dataclass

from app.db.session import get_connection


@dataclass(frozen=True)
class UserRecord:
    id: int
    email: str
    full_name: str
    password_hash: str
    created_at: str


def create_user(email: str, full_name: str, password_hash: str) -> UserRecord:
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (email, full_name, password_hash)
                VALUES (?, ?, ?)
                """,
                (email.lower(), full_name, password_hash),
            )
        except sqlite3.IntegrityError as exc:
            msg = "Email already exists"
            raise ValueError(msg) from exc
        connection.commit()
        user_id = int(cursor.lastrowid)
    user = get_user_by_id(user_id)
    if user is None:
        msg = "Created user could not be loaded"
        raise RuntimeError(msg)
    return user


def get_user_by_email(email: str) -> UserRecord | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, full_name, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (email.lower(),),
        ).fetchone()
    return _row_to_user(row)


def get_user_by_id(user_id: int) -> UserRecord | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, full_name, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_user(row)


def _row_to_user(row: sqlite3.Row | None) -> UserRecord | None:
    if row is None:
        return None
    return UserRecord(
        id=int(row["id"]),
        email=str(row["email"]),
        full_name=str(row["full_name"]),
        password_hash=str(row["password_hash"]),
        created_at=str(row["created_at"]),
    )
