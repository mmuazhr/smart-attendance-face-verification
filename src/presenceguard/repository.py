"""SQLite persistence with transactional duplicate attendance protection."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from presenceguard.domain import AttendanceRecord, AttendanceWrite, ParticipantTemplate


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _serialize_time(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


class SQLiteRepository:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS participants (
                    participant_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    encrypted_template BLOB NOT NULL,
                    template_count INTEGER NOT NULL CHECK (template_count > 0),
                    threshold REAL NOT NULL CHECK (threshold >= -1 AND threshold <= 1),
                    created_at TEXT NOT NULL,
                    consented_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attendance_events (
                    event_id TEXT PRIMARY KEY,
                    participant_id TEXT NOT NULL REFERENCES participants(participant_id)
                        ON DELETE CASCADE,
                    occurred_at TEXT NOT NULL,
                    similarity REAL NOT NULL CHECK (similarity >= -1 AND similarity <= 1),
                    request_id TEXT NOT NULL UNIQUE
                );
                CREATE INDEX IF NOT EXISTS attendance_participant_time
                    ON attendance_events(participant_id, occurred_at DESC);
                """
            )

    def save_participant(
        self,
        *,
        participant_id: str,
        display_name: str,
        encrypted_template: bytes,
        template_count: int,
        threshold: float,
        consented_at: datetime,
    ) -> ParticipantTemplate:
        created_at = _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO participants (
                    participant_id, display_name, encrypted_template, template_count,
                    threshold, created_at, consented_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(participant_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    encrypted_template = excluded.encrypted_template,
                    template_count = excluded.template_count,
                    threshold = excluded.threshold,
                    consented_at = excluded.consented_at
                """,
                (
                    participant_id,
                    display_name,
                    encrypted_template,
                    template_count,
                    threshold,
                    _serialize_time(created_at),
                    _serialize_time(consented_at),
                ),
            )
        stored = self.get_participant(participant_id)
        if stored is None:  # pragma: no cover - defensive database integrity guard
            raise RuntimeError("Participant was not persisted")
        return stored

    def get_participant(self, participant_id: str) -> ParticipantTemplate | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM participants WHERE participant_id = ?", (participant_id,)
            ).fetchone()
        if row is None:
            return None
        return ParticipantTemplate(
            participant_id=row["participant_id"],
            display_name=row["display_name"],
            encrypted_template=bytes(row["encrypted_template"]),
            template_count=int(row["template_count"]),
            threshold=float(row["threshold"]),
            created_at=_parse_time(row["created_at"]),
            consented_at=_parse_time(row["consented_at"]),
        )

    def delete_participant(self, participant_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM participants WHERE participant_id = ?", (participant_id,)
            )
        return cursor.rowcount > 0

    def record_attendance(
        self,
        *,
        participant_id: str,
        similarity: float,
        request_id: str,
        occurred_at: datetime | None = None,
        duplicate_window_seconds: int = 300,
    ) -> AttendanceWrite:
        timestamp = occurred_at or _utc_now()
        cutoff = timestamp - timedelta(seconds=duplicate_window_seconds)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM attendance_events WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing is not None:
                connection.commit()
                return AttendanceWrite(
                    record=self._attendance_from_row(existing),
                    created=False,
                    idempotent_replay=True,
                    blocked_by_window=False,
                )

            recent = connection.execute(
                """
                SELECT * FROM attendance_events
                WHERE participant_id = ? AND occurred_at >= ?
                ORDER BY occurred_at DESC LIMIT 1
                """,
                (participant_id, _serialize_time(cutoff)),
            ).fetchone()
            if recent is not None and duplicate_window_seconds > 0:
                connection.commit()
                return AttendanceWrite(
                    record=self._attendance_from_row(recent),
                    created=False,
                    idempotent_replay=False,
                    blocked_by_window=True,
                )

            event = AttendanceRecord(
                event_id=str(uuid.uuid4()),
                participant_id=participant_id,
                occurred_at=timestamp,
                similarity=similarity,
                request_id=request_id,
            )
            connection.execute(
                """
                INSERT INTO attendance_events (
                    event_id, participant_id, occurred_at, similarity, request_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.participant_id,
                    _serialize_time(event.occurred_at),
                    event.similarity,
                    event.request_id,
                ),
            )
            connection.commit()
            return AttendanceWrite(
                record=event,
                created=True,
                idempotent_replay=False,
                blocked_by_window=False,
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_attendance(
        self, *, participant_id: str | None = None, limit: int = 100
    ) -> list[AttendanceRecord]:
        safe_limit = min(max(limit, 1), 500)
        with self._connect() as connection:
            if participant_id:
                rows = connection.execute(
                    """
                    SELECT * FROM attendance_events WHERE participant_id = ?
                    ORDER BY occurred_at DESC LIMIT ?
                    """,
                    (participant_id, safe_limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM attendance_events ORDER BY occurred_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
        return [self._attendance_from_row(row) for row in rows]

    @staticmethod
    def _attendance_from_row(row: sqlite3.Row) -> AttendanceRecord:
        return AttendanceRecord(
            event_id=row["event_id"],
            participant_id=row["participant_id"],
            occurred_at=_parse_time(row["occurred_at"]),
            similarity=float(row["similarity"]),
            request_id=row["request_id"],
        )
