from __future__ import annotations

from datetime import UTC, datetime, timedelta

from presenceguard.repository import SQLiteRepository


def _save_participant(repository: SQLiteRepository) -> None:
    repository.save_participant(
        participant_id="student-001",
        display_name="Student One",
        encrypted_template=b"encrypted",
        template_count=5,
        threshold=0.55,
        consented_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_attendance_is_transactionally_idempotent_and_debounced(
    repository: SQLiteRepository,
) -> None:
    _save_participant(repository)
    first_time = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)

    first = repository.record_attendance(
        participant_id="student-001",
        similarity=0.9,
        request_id="request-1",
        occurred_at=first_time,
        duplicate_window_seconds=300,
    )
    replay = repository.record_attendance(
        participant_id="student-001",
        similarity=0.9,
        request_id="request-1",
        occurred_at=first_time + timedelta(seconds=10),
        duplicate_window_seconds=300,
    )
    duplicate = repository.record_attendance(
        participant_id="student-001",
        similarity=0.91,
        request_id="request-2",
        occurred_at=first_time + timedelta(seconds=20),
        duplicate_window_seconds=300,
    )
    later = repository.record_attendance(
        participant_id="student-001",
        similarity=0.92,
        request_id="request-3",
        occurred_at=first_time + timedelta(seconds=301),
        duplicate_window_seconds=300,
    )

    assert first.created is True
    assert replay.idempotent_replay is True
    assert replay.record == first.record
    assert duplicate.blocked_by_window is True
    assert duplicate.record == first.record
    assert later.created is True
    assert len(repository.list_attendance()) == 2


def test_deleting_participant_cascades_attendance(repository: SQLiteRepository) -> None:
    _save_participant(repository)
    repository.record_attendance(
        participant_id="student-001", similarity=0.9, request_id="request-1"
    )

    assert repository.delete_participant("student-001") is True
    assert repository.get_participant("student-001") is None
    assert repository.list_attendance() == []
