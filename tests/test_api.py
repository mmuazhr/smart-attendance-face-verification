from __future__ import annotations

from pathlib import Path

from conftest import FakeFaceEngine
from fastapi.testclient import TestClient

from presenceguard.api import create_app
from presenceguard.config import Settings
from presenceguard.crypto import generate_template_key


def _client(tmp_path: Path, engine: FakeFaceEngine) -> TestClient:
    settings = Settings(
        _env_file=None,
        database_path=tmp_path / "api.db",
        template_key=generate_template_key(),
        admin_token="local-admin-token",
        match_threshold=0.8,
        minimum_enrollment_samples=3,
        maximum_enrollment_samples=5,
    )
    return TestClient(create_app(settings, face_engine=engine))


def _files(payloads: list[bytes]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("images", (f"frame-{index}.jpg", payload, "image/jpeg"))
        for index, payload in enumerate(payloads)
    ]


def test_health_home_enrollment_and_verification(
    tmp_path: Path, fake_face_engine: FakeFaceEngine
) -> None:
    client = _client(tmp_path, fake_face_engine)

    assert client.get("/health").json()["image_retention"] == "none"
    assert "Keep faces private" in client.get("/").text

    enrollment = client.post(
        "/api/v1/participants/student-001/enrollment",
        headers={"X-Admin-Token": "local-admin-token"},
        data={"display_name": "Student One", "consent_confirmed": "true"},
        files=_files([b"front", b"angle", b"front"]),
    )
    assert enrollment.status_code == 200
    assert enrollment.json()["accepted_samples"] == 3

    verification = client.post(
        "/api/v1/participants/student-001/verification",
        headers={"Idempotency-Key": "api-request-1"},
        files={"image": ("frame.jpg", b"angle", "image/jpeg")},
    )
    assert verification.status_code == 200
    assert verification.json()["status"] == "verified"

    unauthorized = client.get("/api/v1/attendance")
    assert unauthorized.status_code == 403
    authorized = client.get("/api/v1/attendance", headers={"X-Admin-Token": "local-admin-token"})
    assert authorized.status_code == 200
    assert len(authorized.json()) == 1


def test_api_rejects_invalid_media_and_returns_stable_error_shape(
    tmp_path: Path, fake_face_engine: FakeFaceEngine
) -> None:
    client = _client(tmp_path, fake_face_engine)
    response = client.post(
        "/api/v1/participants/student-001/verification",
        headers={"Idempotency-Key": "api-request-2"},
        files={"image": ("payload.txt", b"front", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_image",
            "message": "Only JPEG, PNG, and WebP images are accepted",
        }
    }


def test_enrollment_requires_admin_token(tmp_path: Path, fake_face_engine: FakeFaceEngine) -> None:
    client = _client(tmp_path, fake_face_engine)
    response = client.post(
        "/api/v1/participants/student-001/enrollment",
        data={"display_name": "Student One", "consent_confirmed": "true"},
        files=_files([b"front", b"angle", b"front"]),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_access_denied"
