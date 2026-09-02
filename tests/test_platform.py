from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from conftest import FakeFaceEngine
from fastapi.testclient import TestClient

from presenceguard.api import create_app
from presenceguard.config import Settings
from presenceguard.crypto import generate_template_key


def _platform_clients(tmp_path: Path, engine: FakeFaceEngine) -> tuple[TestClient, TestClient]:
    settings = Settings(
        _env_file=None,
        database_path=tmp_path / "platform.db",
        template_key=generate_template_key(),
        admin_token="local-admin-token",
        admin_password="local-admin-token",
        match_threshold=0.8,
        minimum_enrollment_samples=3,
        maximum_enrollment_samples=5,
    )
    application = create_app(settings, face_engine=engine)
    return TestClient(application), TestClient(application)


def _session_payload() -> dict[str, str]:
    today = datetime.now(UTC).date().isoformat()
    return {
        "title": "Software Engineering Lecture",
        "description": "A real persisted session",
        "course": "CSC3102",
        "location": "Lab 4",
        "session_date": today,
        "start_time": "00:00",
        "end_time": "23:59",
        "check_in_open": "00:00",
        "check_in_close": "23:59",
        "late_threshold": "23:59",
    }


def test_platform_roles_sessions_checkin_duplicate_and_audit(
    tmp_path: Path, fake_face_engine: FakeFaceEngine
) -> None:
    admin, participant = _platform_clients(tmp_path, fake_face_engine)

    login = admin.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "local-admin-token"},
    )
    assert login.status_code == 200
    created = admin.post(
        "/api/v1/admin/participants",
        json={
            "participant_id": "student-001",
            "username": "student001",
            "email": "student@example.edu",
            "display_name": "Student One",
            "password": "student-password",
        },
    )
    assert created.status_code == 200

    session = admin.post("/api/v1/admin/sessions", json=_session_payload())
    assert session.status_code == 200
    session_id = session.json()["session"]["session_id"]
    activated = admin.patch(
        f"/api/v1/admin/sessions/{session_id}/status", json={"status": "active"}
    )
    assert activated.status_code == 200

    assert admin.get("/api/v1/admin/dashboard").status_code == 200
    assert participant.get("/api/v1/admin/dashboard").status_code == 401

    assert (
        participant.post(
            "/api/v1/auth/login",
            json={"username": "student001", "password": "student-password"},
        ).status_code
        == 200
    )
    assert participant.get("/api/v1/admin/dashboard").status_code == 403
    enrollment = participant.post(
        "/api/v1/me/enrollment",
        data={"consent_confirmed": "true"},
        files=[
            ("images", ("one.jpg", b"front", "image/jpeg")),
            ("images", ("two.jpg", b"angle", "image/jpeg")),
            ("images", ("three.jpg", b"front", "image/jpeg")),
        ],
    )
    assert enrollment.status_code == 200

    first = participant.post(
        f"/api/v1/sessions/{session_id}/check-in",
        headers={"Idempotency-Key": "platform-request-1"},
        files={"image": ("frame.jpg", b"angle", "image/jpeg")},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "verified"
    duplicate = participant.post(
        f"/api/v1/sessions/{session_id}/check-in",
        headers={"Idempotency-Key": "platform-request-2"},
        files={"image": ("frame.jpg", b"front", "image/jpeg")},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"
    assert len(participant.get("/api/v1/attendance/history").json()) == 1

    attendance_id = participant.get("/api/v1/attendance/history").json()[0]["attendance_id"]
    corrected = admin.patch(
        f"/api/v1/admin/attendance/{attendance_id}",
        json={"status": "excused", "reason": "Approved medical leave"},
    )
    assert corrected.status_code == 200
    assert corrected.json()["attendance"]["status"] == "excused"
    assert any(
        item["action"] == "attendance.corrected"
        for item in admin.get("/api/v1/admin/audit-logs").json()
    )
