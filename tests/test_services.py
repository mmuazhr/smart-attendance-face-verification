from __future__ import annotations

import pytest
from conftest import FakeFaceEngine

from presenceguard.crypto import TemplateCipher, generate_template_key
from presenceguard.domain import VerificationStatus
from presenceguard.errors import ConsentRequiredError, InvalidRequestError
from presenceguard.repository import SQLiteRepository
from presenceguard.services import EnrollmentService, VerificationService


def _services(
    engine: FakeFaceEngine, repository: SQLiteRepository
) -> tuple[EnrollmentService, VerificationService]:
    cipher = TemplateCipher(generate_template_key())
    return (
        EnrollmentService(
            engine,
            cipher,
            repository,
            threshold=0.8,
            minimum_samples=3,
            maximum_samples=5,
        ),
        VerificationService(engine, cipher, repository, duplicate_window_seconds=300),
    )


def test_enrollment_verification_rejection_and_duplicate_window(
    fake_face_engine: FakeFaceEngine, repository: SQLiteRepository
) -> None:
    enrollment, verification = _services(fake_face_engine, repository)
    enrolled = enrollment.enroll(
        participant_id="student-001",
        display_name="Student One",
        images=[b"front", b"angle", b"front", b"bad"],
        consent_confirmed=True,
    )

    assert enrolled.accepted_samples == 3
    assert enrolled.rejected_samples == 1

    accepted = verification.verify(
        participant_id="student-001", image=b"angle", request_id="request-1"
    )
    duplicate = verification.verify(
        participant_id="student-001", image=b"front", request_id="request-2"
    )
    rejected = verification.verify(
        participant_id="student-001", image=b"other", request_id="request-3"
    )

    assert accepted.status is VerificationStatus.VERIFIED
    assert accepted.event_id is not None
    assert duplicate.status is VerificationStatus.DUPLICATE
    assert duplicate.event_id == accepted.event_id
    assert rejected.status is VerificationStatus.REJECTED
    assert rejected.reason == "below_threshold"
    assert len(repository.list_attendance()) == 1


def test_enrollment_requires_consent_and_enough_valid_samples(
    fake_face_engine: FakeFaceEngine, repository: SQLiteRepository
) -> None:
    enrollment, _ = _services(fake_face_engine, repository)
    with pytest.raises(ConsentRequiredError):
        enrollment.enroll(
            participant_id="student-001",
            display_name="Student One",
            images=[b"front"] * 3,
            consent_confirmed=False,
        )
    with pytest.raises(InvalidRequestError):
        enrollment.enroll(
            participant_id="student-001",
            display_name="Student One",
            images=[b"bad"] * 3,
            consent_confirmed=True,
        )
