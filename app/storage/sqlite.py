from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ReminderRecord:
    reminder_id: int
    chat_id: int
    reminder_type: str
    due_at: datetime
    payload: dict[str, Any]


class SQLiteStorage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def init(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    chat_id INTEGER PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    sent_at TEXT,
                    canceled_at TEXT
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    lead_id INTEGER,
                    task_id INTEGER,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS completed_chats (
                    chat_id INTEGER PRIMARY KEY,
                    payload TEXT NOT NULL,
                    completed_at TEXT NOT NULL
                );
                """
            )

    def get_session(self, chat_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM sessions WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, chat_id: int, payload: dict[str, Any]) -> None:
        now = utcnow().isoformat()
        serialized = json.dumps(payload, ensure_ascii=False)
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions (chat_id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (chat_id, serialized, now),
            )

    def delete_session(self, chat_id: int) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))

    def schedule_reminder(
        self,
        chat_id: int,
        reminder_type: str,
        due_at: datetime,
        payload: dict[str, Any],
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO reminders (chat_id, reminder_type, due_at, payload, sent_at, canceled_at)
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (chat_id, reminder_type, due_at.isoformat(), json.dumps(payload, ensure_ascii=False)),
            )

    def cancel_pending_reminders(self, chat_id: int, reminder_type: str | None = None) -> None:
        now = utcnow().isoformat()
        query = """
            UPDATE reminders
            SET canceled_at = ?
            WHERE chat_id = ?
              AND sent_at IS NULL
              AND canceled_at IS NULL
        """
        params: list[Any] = [now, chat_id]
        if reminder_type is not None:
            query += " AND reminder_type = ?"
            params.append(reminder_type)

        with self._connection() as connection:
            connection.execute(query, params)

    def list_due_reminders(self, now: datetime) -> list[ReminderRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, chat_id, reminder_type, due_at, payload
                FROM reminders
                WHERE sent_at IS NULL
                  AND canceled_at IS NULL
                  AND due_at <= ?
                ORDER BY due_at ASC
                """,
                (now.isoformat(),),
            ).fetchall()

        return [
            ReminderRecord(
                reminder_id=row[0],
                chat_id=row[1],
                reminder_type=row[2],
                due_at=datetime.fromisoformat(row[3]),
                payload=json.loads(row[4]),
            )
            for row in rows
        ]

    def mark_reminder_sent(self, reminder_id: int) -> None:
        with self._connection() as connection:
            connection.execute(
                "UPDATE reminders SET sent_at = ? WHERE id = ?",
                (utcnow().isoformat(), reminder_id),
            )

    def save_submission(
        self,
        chat_id: int,
        status: str,
        score: int,
        payload: dict[str, Any],
        lead_id: int | None,
        task_id: int | None,
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO submissions (chat_id, created_at, status, score, lead_id, task_id, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    utcnow().isoformat(),
                    status,
                    score,
                    lead_id,
                    task_id,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def save_completed_chat(self, chat_id: int, payload: dict[str, Any]) -> None:
        now = utcnow().isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO completed_chats (chat_id, payload, completed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    payload = excluded.payload,
                    completed_at = excluded.completed_at
                """,
                (chat_id, json.dumps(payload, ensure_ascii=False), now),
            )

    def get_completed_chat(self, chat_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload FROM completed_chats WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def delete_completed_chat(self, chat_id: int) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM completed_chats WHERE chat_id = ?", (chat_id,))

    def clear_website_handoff_sessions(self) -> int:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT chat_id
                FROM sessions
                WHERE payload LIKE '%website_request_id%'
                """
            ).fetchall()
            chat_ids = [row[0] for row in rows]
            for chat_id in chat_ids:
                connection.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
                connection.execute(
                    """
                    UPDATE reminders
                    SET canceled_at = ?
                    WHERE chat_id = ?
                      AND sent_at IS NULL
                      AND canceled_at IS NULL
                    """,
                    (utcnow().isoformat(), chat_id),
                )
        return len(chat_ids)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> sqlite3.Connection:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
