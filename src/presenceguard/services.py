"""Application services for enrollment, verification, and privacy controls."""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import numpy as np

from presenceguard.crypto import TemplateCipher
from presenceguard.domain import EnrollmentResult, VerificationResult, VerificationStatus
from presenceguard.errors import (
    ConsentRequiredError,
    InvalidRequestError,
    ParticipantNotFoundError,
    PresenceGuardError,
)
from presenceguard.face import FaceEngine
from presenceguard.repository import SQLiteRepository

_PARTICIPANT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")


def _validate_identity(participant_id: str, display_name: str | None = None) -> None:
    if not _PARTICIPANT_ID.fullmatch(participant_id):
        raise InvalidRequestError(
            "Participant ID must be 3-64 characters using letters, numbers, underscore, or dash"
        )
    if display_name is not None and not 1 <= len(display_name.strip()) <= 100:
        raise InvalidRequestError("Display name must contain 1-100 characters")


class EnrollmentService:
    def __init__(
        self,
        face_engine: FaceEngine,
        cipher: TemplateCipher,
        repository: SQLiteRepository,
        *,
        threshold: float,
        minimum_samples: int = 5,
        maximum_samples: int = 50,
    ):
        self._face_engine = face_engine
        self._cipher = cipher
        self._repository = repository
        self._threshold = threshold
        self._minimum_samples = minimum_samples
        self._maximum_samples = maximum_samples

    def enroll(
        self,
        *,
        participant_id: str,
        display_name: str,
        images: Sequence[bytes],
        consent_confirmed: bool,
    ) -> EnrollmentResult:
        _validate_identity(participant_id, display_name)
        if not consent_confirmed:
            raise ConsentRequiredError("Explicit biometric enrollment consent is required")
        if not self._minimum_samples <= len(images) <= self._maximum_samples:
            raise InvalidRequestError(
                f"Provide {self._minimum_samples}-{self._maximum_samples} enrollment images"
            )

        embeddings: list[np.ndarray] = []
        rejected = 0
        for image in images:
            try:
                observation = self._face_engine.extract(image)
            except PresenceGuardError:
                rejected += 1
                continue
            embeddings.append(observation.embedding)
        if len(embeddings) < self._minimum_samples:
            raise InvalidRequestError(
                f"Only {len(embeddings)} usable samples; "
                f"at least {self._minimum_samples} are required"
            )

        matrix = np.stack(embeddings).astype(np.float32)
        encrypted = self._cipher.encrypt(participant_id, matrix)
        self._repository.save_participant(
            participant_id=participant_id,
            display_name=display_name.strip(),
            encrypted_template=encrypted,
            template_count=len(embeddings),
            threshold=self._threshold,
            consented_at=datetime.now(UTC),
        )
        return EnrollmentResult(
            participant_id=participant_id,
            accepted_samples=len(embeddings),
            rejected_samples=rejected,
            threshold=self._threshold,
        )


class VerificationService:
    def __init__(
        self,
        face_engine: FaceEngine,
        cipher: TemplateCipher,
        repository: SQLiteRepository,
        *,
        duplicate_window_seconds: int = 300,
    ):
        self._face_engine = face_engine
        self._cipher = cipher
        self._repository = repository
        self._duplicate_window_seconds = duplicate_window_seconds

    def verify(
        self, *, participant_id: str, image: bytes, request_id: str | None = None
    ) -> VerificationResult:
        _validate_identity(participant_id)
        participant = self._repository.get_participant(participant_id)
        if participant is None:
            raise ParticipantNotFoundError("Participant is not enrolled")

        observation = self._face_engine.extract(image)
        references = self._cipher.decrypt(participant_id, participant.encrypted_template)
        if references.shape[1] != observation.embedding.size:
            raise InvalidRequestError("Stored template is incompatible with the face model")
        score = float(np.max(references @ observation.embedding))
        if not np.isfinite(score):
            raise InvalidRequestError("Verification score is invalid")
        if score < participant.threshold:
            return VerificationResult(
                participant_id=participant_id,
                status=VerificationStatus.REJECTED,
                score=score,
                threshold=participant.threshold,
                reason="below_threshold",
            )

        safe_request_id = request_id or str(uuid.uuid4())
        if len(safe_request_id) > 128:
            raise InvalidRequestError("Request ID exceeds 128 characters")
        write = self._repository.record_attendance(
            participant_id=participant_id,
            similarity=score,
            request_id=safe_request_id,
            duplicate_window_seconds=self._duplicate_window_seconds,
        )
        if write.blocked_by_window:
            return VerificationResult(
                participant_id=participant_id,
                status=VerificationStatus.DUPLICATE,
                score=score,
                threshold=participant.threshold,
                event_id=write.record.event_id if write.record else None,
                occurred_at=write.record.occurred_at if write.record else None,
                reason="duplicate_window",
            )
        if write.record is None:  # pragma: no cover - repository invariant
            raise RuntimeError("Attendance repository returned no record")
        return VerificationResult(
            participant_id=participant_id,
            status=VerificationStatus.VERIFIED,
            score=score,
            threshold=participant.threshold,
            event_id=write.record.event_id,
            occurred_at=write.record.occurred_at,
            idempotent_replay=write.idempotent_replay,
        )

    def delete_participant(self, participant_id: str) -> bool:
        _validate_identity(participant_id)
        return self._repository.delete_participant(participant_id)
