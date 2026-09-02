"""SQLite persistence with transactional duplicate attendance protection."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from presenceguard.auth import hash_password
from presenceguard.domain import (
    AccountStatus,
    AttendanceRecord,
    AttendanceSession,
    AttendanceStatus,
    AttendanceWrite,
    AuditLog,
    LivenessStatus,
    ParticipantTemplate,
    PlatformAttendanceRecord,
    SessionStatus,
    UserRecord,
    UserRole,
    VerificationAttempt,
    VerificationMethod,
    VerificationStatus,
)


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

                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'participant')),
                    status TEXT NOT NULL CHECK (status IN ('active', 'disabled')),
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attendance_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    course TEXT NOT NULL,
                    location TEXT NOT NULL DEFAULT '',
                    session_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    check_in_open TEXT NOT NULL,
                    check_in_close TEXT NOT NULL,
                    late_threshold TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (
                        status IN ('draft', 'scheduled', 'active', 'closed', 'archived')
                    ),
                    created_by TEXT NOT NULL REFERENCES users(user_id),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS attendance_sessions_date
                    ON attendance_sessions(session_date, status);
                CREATE TABLE IF NOT EXISTS attendance_records (
                    attendance_id TEXT PRIMARY KEY,
                    participant_id TEXT NOT NULL REFERENCES users(user_id),
                    session_id TEXT NOT NULL REFERENCES attendance_sessions(session_id),
                    status TEXT NOT NULL CHECK (
                        status IN ('present', 'late', 'absent', 'excused', 'manually_added')
                    ),
                    check_in_timestamp TEXT,
                    verification_method TEXT NOT NULL,
                    face_verification_score REAL,
                    liveness_result TEXT NOT NULL,
                    manually_adjusted INTEGER NOT NULL DEFAULT 0 CHECK (
                        manually_adjusted IN (0, 1)
                    ),
                    adjustment_reason TEXT,
                    adjusted_by TEXT REFERENCES users(user_id),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(participant_id, session_id)
                );
                CREATE INDEX IF NOT EXISTS attendance_records_session
                    ON attendance_records(session_id, status);
                CREATE TABLE IF NOT EXISTS verification_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    participant_id TEXT NOT NULL,
                    session_id TEXT REFERENCES attendance_sessions(session_id),
                    occurred_at TEXT NOT NULL,
                    face_detected INTEGER NOT NULL CHECK (face_detected IN (0, 1)),
                    face_verification_result TEXT NOT NULL,
                    liveness_result TEXT NOT NULL,
                    final_result TEXT NOT NULL,
                    failure_reason TEXT
                );
                CREATE INDEX IF NOT EXISTS verification_attempts_time
                    ON verification_attempts(occurred_at DESC);
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    actor_user_id TEXT REFERENCES users(user_id),
                    action TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    reason TEXT,
                    occurred_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS audit_logs_time
                    ON audit_logs(occurred_at DESC);
                """
            )

    def ensure_bootstrap_admin(self, *, username: str, password: str) -> UserRecord:
        if not password:
            raise ValueError("A bootstrap admin password is required")
        existing = self.get_user_by_username(username)
        if existing is not None:
            return existing
        now = _utc_now()
        return self.create_user(
            user_id=f"admin-{uuid.uuid4().hex[:12]}",
            username=username,
            email=f"{username}@localhost",
            display_name="Local Administrator",
            role=UserRole.ADMIN,
            password=password,
            created_at=now,
        )

    def create_user(
        self,
        *,
        user_id: str,
        username: str,
        email: str,
        display_name: str,
        role: UserRole,
        password: str,
        created_at: datetime | None = None,
    ) -> UserRecord:
        now = created_at or _utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    user_id, username, email, display_name, role, status, password_hash,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    email,
                    display_name,
                    role.value,
                    AccountStatus.ACTIVE.value,
                    hash_password(password),
                    _serialize_time(now),
                    _serialize_time(now),
                ),
            )
        stored = self.get_user(user_id)
        if stored is None:  # pragma: no cover
            raise RuntimeError("User was not persisted")
        return stored

    def get_user(self, user_id: str) -> UserRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return self._user_from_row(row) if row else None

    def get_user_by_username(self, username: str) -> UserRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        return self._user_from_row(row) if row else None

    def list_users(
        self, *, role: UserRole | None = None, include_disabled: bool = True
    ) -> list[UserRecord]:
        values: list[str] = []
        if role is not None:
            values.append(role.value)
        with self._connect() as connection:
            if role is None and include_disabled:
                rows = connection.execute(
                    "SELECT * FROM users ORDER BY display_name COLLATE NOCASE"
                ).fetchall()
            elif role is not None and include_disabled:
                rows = connection.execute(
                    "SELECT * FROM users WHERE role = ? ORDER BY display_name COLLATE NOCASE",
                    values,
                ).fetchall()
            elif role is None:
                rows = connection.execute(
                    "SELECT * FROM users WHERE status = 'active' "
                    "ORDER BY display_name COLLATE NOCASE"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM users WHERE role = ? AND status = 'active' "
                    "ORDER BY display_name COLLATE NOCASE",
                    values,
                ).fetchall()
        return [self._user_from_row(row) for row in rows]

    def update_user_status(self, user_id: str, status: AccountStatus) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE users SET status = ?, updated_at = ? WHERE user_id = ?",
                (status.value, _serialize_time(_utc_now()), user_id),
            )
        return cursor.rowcount > 0

    def create_session(
        self,
        *,
        title: str,
        description: str,
        course: str,
        location: str,
        session_date: str,
        start_time: str,
        end_time: str,
        check_in_open: str,
        check_in_close: str,
        late_threshold: str,
        created_by: str,
        status: SessionStatus = SessionStatus.SCHEDULED,
    ) -> AttendanceSession:
        session = AttendanceSession(
            session_id=f"ses-{uuid.uuid4().hex[:12]}",
            title=title,
            description=description,
            course=course,
            location=location,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            check_in_open=check_in_open,
            check_in_close=check_in_close,
            late_threshold=late_threshold,
            status=status,
            created_by=created_by,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO attendance_sessions (
                    session_id, title, description, course, location, session_date,
                    start_time, end_time, check_in_open, check_in_close, late_threshold,
                    status, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.title,
                    session.description,
                    session.course,
                    session.location,
                    session.session_date,
                    session.start_time,
                    session.end_time,
                    session.check_in_open,
                    session.check_in_close,
                    session.late_threshold,
                    session.status.value,
                    session.created_by,
                    _serialize_time(session.created_at),
                    _serialize_time(session.updated_at),
                ),
            )
        return session

    def get_session(self, session_id: str) -> AttendanceSession | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM attendance_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return self._session_from_row(row) if row else None

    def list_sessions(self, *, include_archived: bool = False) -> list[AttendanceSession]:
        with self._connect() as connection:
            if include_archived:
                rows = connection.execute(
                    "SELECT * FROM attendance_sessions ORDER BY session_date DESC, start_time DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM attendance_sessions WHERE status != 'archived' "
                    "ORDER BY session_date DESC, start_time DESC"
                ).fetchall()
        return [self._session_from_row(row) for row in rows]

    def update_session_status(
        self, session_id: str, status: SessionStatus
    ) -> AttendanceSession | None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE attendance_sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status.value, _serialize_time(_utc_now()), session_id),
            )
        return self.get_session(session_id)

    def update_session_details(
        self, session_id: str, details: dict[str, str]
    ) -> AttendanceSession | None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE attendance_sessions SET title = ?, description = ?, course = ?, location = ?,
                    session_date = ?, start_time = ?, end_time = ?, check_in_open = ?,
                    check_in_close = ?, late_threshold = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (
                    details["title"],
                    details["description"],
                    details["course"],
                    details["location"],
                    details["session_date"],
                    details["start_time"],
                    details["end_time"],
                    details["check_in_open"],
                    details["check_in_close"],
                    details["late_threshold"],
                    _serialize_time(_utc_now()),
                    session_id,
                ),
            )
        return self.get_session(session_id)

    def list_session_roster(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT u.user_id, u.username, u.email, u.display_name, u.status AS account_status,
                       ar.attendance_id, ar.status AS attendance_status, ar.check_in_timestamp,
                       ar.verification_method, ar.face_verification_score, ar.liveness_result,
                       ar.manually_adjusted, ar.adjustment_reason, ar.adjusted_by
                FROM users u
                LEFT JOIN attendance_records ar
                  ON ar.participant_id = u.user_id AND ar.session_id = ?
                WHERE u.role = 'participant'
                ORDER BY u.display_name COLLATE NOCASE
                """,
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_platform_attendance(
        self, *, participant_id: str | None = None, session_id: str | None = None
    ) -> list[PlatformAttendanceRecord]:
        values: list[str] = []
        if participant_id:
            values.append(participant_id)
        if session_id:
            values.append(session_id)
        with self._connect() as connection:
            if participant_id and session_id:
                rows = connection.execute(
                    "SELECT * FROM attendance_records "
                    "WHERE participant_id = ? AND session_id = ? "
                    "ORDER BY COALESCE(check_in_timestamp, created_at) DESC",
                    values,
                ).fetchall()
            elif participant_id:
                rows = connection.execute(
                    "SELECT * FROM attendance_records WHERE participant_id = ? "
                    "ORDER BY COALESCE(check_in_timestamp, created_at) DESC",
                    values,
                ).fetchall()
            elif session_id:
                rows = connection.execute(
                    "SELECT * FROM attendance_records WHERE session_id = ? "
                    "ORDER BY COALESCE(check_in_timestamp, created_at) DESC",
                    values,
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM attendance_records "
                    "ORDER BY COALESCE(check_in_timestamp, created_at) DESC"
                ).fetchall()
        return [self._platform_attendance_from_row(row) for row in rows]

    def get_platform_attendance(self, attendance_id: str) -> PlatformAttendanceRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM attendance_records WHERE attendance_id = ?", (attendance_id,)
            ).fetchone()
        return self._platform_attendance_from_row(row) if row else None

    def record_platform_attendance(
        self,
        *,
        participant_id: str,
        session_id: str,
        status: AttendanceStatus,
        verification_method: VerificationMethod,
        face_verification_score: float | None,
        liveness_result: LivenessStatus,
        check_in_timestamp: datetime | None,
        request_id: str,
    ) -> tuple[PlatformAttendanceRecord, bool]:
        now = _utc_now()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM attendance_records WHERE participant_id = ? AND session_id = ?",
                (participant_id, session_id),
            ).fetchone()
            if existing:
                connection.commit()
                return self._platform_attendance_from_row(existing), False
            attendance_id = f"att-{uuid.uuid4().hex[:12]}"
            connection.execute(
                """
                INSERT INTO attendance_records (
                    attendance_id, participant_id, session_id, status, check_in_timestamp,
                    verification_method, face_verification_score, liveness_result,
                    manually_adjusted, adjustment_reason, adjusted_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, ?, ?)
                """,
                (
                    attendance_id,
                    participant_id,
                    session_id,
                    status.value,
                    _serialize_time(check_in_timestamp) if check_in_timestamp else None,
                    verification_method.value,
                    face_verification_score,
                    liveness_result.value,
                    _serialize_time(now),
                    _serialize_time(now),
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        record = self.get_platform_attendance(attendance_id)
        if record is None:  # pragma: no cover
            raise RuntimeError("Attendance record was not persisted")
        return record, True

    def correct_attendance(
        self,
        *,
        attendance_id: str,
        status: AttendanceStatus,
        reason: str,
        adjusted_by: str,
    ) -> PlatformAttendanceRecord | None:
        now = _serialize_time(_utc_now())
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE attendance_records SET status = ?, manually_adjusted = 1,
                    adjustment_reason = ?, adjusted_by = ?, updated_at = ?
                WHERE attendance_id = ?
                """,
                (status.value, reason, adjusted_by, now, attendance_id),
            )
        return self.get_platform_attendance(attendance_id)

    def add_verification_attempt(
        self,
        *,
        participant_id: str,
        session_id: str | None,
        face_detected: bool,
        face_verification_result: VerificationStatus,
        liveness_result: LivenessStatus,
        final_result: str,
        failure_reason: str | None,
    ) -> VerificationAttempt:
        attempt = VerificationAttempt(
            attempt_id=f"try-{uuid.uuid4().hex[:12]}",
            participant_id=participant_id,
            session_id=session_id,
            occurred_at=_utc_now(),
            face_detected=face_detected,
            face_verification_result=face_verification_result,
            liveness_result=liveness_result,
            final_result=final_result,
            failure_reason=failure_reason,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO verification_attempts (
                    attempt_id, participant_id, session_id, occurred_at, face_detected,
                    face_verification_result, liveness_result, final_result, failure_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt.attempt_id,
                    attempt.participant_id,
                    attempt.session_id,
                    _serialize_time(attempt.occurred_at),
                    int(attempt.face_detected),
                    attempt.face_verification_result.value,
                    attempt.liveness_result.value,
                    attempt.final_result,
                    attempt.failure_reason,
                ),
            )
        return attempt

    def list_verification_attempts(
        self, *, limit: int = 100, failures_only: bool = False
    ) -> list[dict[str, Any]]:
        safe_limit = min(max(limit, 1), 500)
        with self._connect() as connection:
            if failures_only:
                rows = connection.execute(
                    "SELECT * FROM verification_attempts WHERE final_result != 'verified' "
                    "ORDER BY occurred_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM verification_attempts ORDER BY occurred_at DESC LIMIT ?",
                    (safe_limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def add_audit_log(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        target_type: str,
        target_id: str,
        metadata: str = "{}",
        reason: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            audit_id=f"aud-{uuid.uuid4().hex[:12]}",
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            reason=reason,
            occurred_at=_utc_now(),
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_logs (
                    audit_id, actor_user_id, action, target_type, target_id, metadata,
                    reason, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.audit_id,
                    entry.actor_user_id,
                    entry.action,
                    entry.target_type,
                    entry.target_id,
                    entry.metadata,
                    entry.reason,
                    _serialize_time(entry.occurred_at),
                ),
            )
        return entry

    def list_audit_logs(self, *, limit: int = 100) -> list[AuditLog]:
        safe_limit = min(max(limit, 1), 500)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_logs ORDER BY occurred_at DESC LIMIT ?", (safe_limit,)
            ).fetchall()
        return [
            AuditLog(
                audit_id=row["audit_id"],
                actor_user_id=row["actor_user_id"],
                action=row["action"],
                target_type=row["target_type"],
                target_id=row["target_id"],
                metadata=row["metadata"],
                reason=row["reason"],
                occurred_at=_parse_time(row["occurred_at"]),
            )
            for row in rows
        ]

    def participant_summary(self, participant_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(ar.attendance_id) AS total,
                       SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) AS present,
                       SUM(CASE WHEN ar.status = 'late' THEN 1 ELSE 0 END) AS late,
                       SUM(CASE WHEN ar.status = 'absent' THEN 1 ELSE 0 END) AS absent,
                       SUM(CASE WHEN ar.status = 'excused' THEN 1 ELSE 0 END) AS excused
                FROM attendance_records ar WHERE ar.participant_id = ?
                """,
                (participant_id,),
            ).fetchone()
        values = dict(row) if row else {}
        total = int(values.get("total") or 0)
        present = int(values.get("present") or 0)
        late = int(values.get("late") or 0)
        denominator = total
        values["total"] = total
        values["present"] = present
        values["late"] = late
        values["absent"] = int(values.get("absent") or 0)
        values["excused"] = int(values.get("excused") or 0)
        values["attendance_rate"] = (
            round(((present + late) / denominator) * 100, 1) if denominator else 0.0
        )
        return values

    def dashboard_summary(self) -> dict[str, Any]:
        today = datetime.now(UTC).date().isoformat()
        with self._connect() as connection:
            users = connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'participant' AND status = 'active'"
            ).fetchone()[0]
            sessions = connection.execute(
                "SELECT COUNT(*) FROM attendance_sessions WHERE status = 'active'"
            ).fetchone()[0]
            today_records = connection.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) AS present,
                       SUM(CASE WHEN ar.status = 'late' THEN 1 ELSE 0 END) AS late
                FROM attendance_records ar
                JOIN attendance_sessions s ON s.session_id = ar.session_id
                WHERE s.session_date = ?
                """,
                (today,),
            ).fetchone()
            failures = connection.execute(
                "SELECT COUNT(*) FROM verification_attempts WHERE final_result != 'verified'"
            ).fetchone()[0]
        total = int(today_records["total"] or 0)
        present = int(today_records["present"] or 0)
        late = int(today_records["late"] or 0)
        return {
            "total_users": int(users),
            "active_sessions": int(sessions),
            "attendance_today": total,
            "present_today": present,
            "late_today": late,
            "verification_failures": int(failures),
            "attendance_rate": round(((present + late) / total) * 100, 1) if total else 0.0,
        }

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

    @staticmethod
    def _user_from_row(row: sqlite3.Row) -> UserRecord:
        return UserRecord(
            user_id=row["user_id"],
            username=row["username"],
            email=row["email"],
            display_name=row["display_name"],
            role=UserRole(row["role"]),
            status=AccountStatus(row["status"]),
            password_hash=row["password_hash"],
            created_at=_parse_time(row["created_at"]),
            updated_at=_parse_time(row["updated_at"]),
        )

    @staticmethod
    def _session_from_row(row: sqlite3.Row) -> AttendanceSession:
        return AttendanceSession(
            session_id=row["session_id"],
            title=row["title"],
            description=row["description"],
            course=row["course"],
            location=row["location"],
            session_date=row["session_date"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            check_in_open=row["check_in_open"],
            check_in_close=row["check_in_close"],
            late_threshold=row["late_threshold"],
            status=SessionStatus(row["status"]),
            created_by=row["created_by"],
            created_at=_parse_time(row["created_at"]),
            updated_at=_parse_time(row["updated_at"]),
        )

    @staticmethod
    def _platform_attendance_from_row(row: sqlite3.Row) -> PlatformAttendanceRecord:
        return PlatformAttendanceRecord(
            attendance_id=row["attendance_id"],
            participant_id=row["participant_id"],
            session_id=row["session_id"],
            status=AttendanceStatus(row["status"]),
            check_in_timestamp=(
                _parse_time(row["check_in_timestamp"]) if row["check_in_timestamp"] else None
            ),
            verification_method=VerificationMethod(row["verification_method"]),
            face_verification_score=(
                float(row["face_verification_score"])
                if row["face_verification_score"] is not None
                else None
            ),
            liveness_result=LivenessStatus(row["liveness_result"]),
            manually_adjusted=bool(row["manually_adjusted"]),
            adjustment_reason=row["adjustment_reason"],
            adjusted_by=row["adjusted_by"],
            created_at=_parse_time(row["created_at"]),
            updated_at=_parse_time(row["updated_at"]),
        )
