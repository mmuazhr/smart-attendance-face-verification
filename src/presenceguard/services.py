"""Application services for enrollment, verification, and privacy controls."""

from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import numpy as np

from presenceguard.crypto import TemplateCipher
from presenceguard.domain import (
    AttendanceStatus,
    EnrollmentResult,
    LivenessStatus,
    SessionStatus,
    VerificationMethod,
    VerificationResult,
    VerificationStatus,
)
from presenceguard.errors import (
    ConsentRequiredError,
    InvalidRequestError,
    ParticipantNotFoundError,
    PresenceGuardError,
    SessionClosedError,
    SessionNotFoundError,
)
from presenceguard.face import FaceEngine
from presenceguard.liveness import LivenessProvider
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
        result = self.verify_identity(participant_id=participant_id, image=image)
        if result.status is not VerificationStatus.VERIFIED:
            return result

        safe_request_id = request_id or str(uuid.uuid4())
        if len(safe_request_id) > 128:
            raise InvalidRequestError("Request ID exceeds 128 characters")
        write = self._repository.record_attendance(
            participant_id=participant_id,
            similarity=result.score,
            request_id=safe_request_id,
            duplicate_window_seconds=self._duplicate_window_seconds,
        )
        if write.blocked_by_window:
            return VerificationResult(
                participant_id=participant_id,
                status=VerificationStatus.DUPLICATE,
                score=result.score,
                threshold=result.threshold,
                event_id=write.record.event_id if write.record else None,
                occurred_at=write.record.occurred_at if write.record else None,
                reason="duplicate_window",
            )
        if write.record is None:  # pragma: no cover - repository invariant
            raise RuntimeError("Attendance repository returned no record")
        return VerificationResult(
            participant_id=participant_id,
            status=VerificationStatus.VERIFIED,
            score=result.score,
            threshold=result.threshold,
            event_id=write.record.event_id,
            occurred_at=write.record.occurred_at,
            idempotent_replay=write.idempotent_replay,
        )

    def verify_identity(self, *, participant_id: str, image: bytes) -> VerificationResult:
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
        return VerificationResult(
            participant_id=participant_id,
            status=VerificationStatus.VERIFIED,
            score=score,
            threshold=participant.threshold,
        )

    def delete_participant(self, participant_id: str) -> bool:
        _validate_identity(participant_id)
        return self._repository.delete_participant(participant_id)


class AttendanceService:
    """Authenticated attendance policy and biometric transaction orchestration."""

    def __init__(
        self,
        repository: SQLiteRepository,
        verification: VerificationService,
        liveness: LivenessProvider,
        *,
        liveness_required: bool = False,
    ):
        self._repository = repository
        self._verification = verification
        self._liveness = liveness
        self._liveness_required = liveness_required

    @staticmethod
    def _boundary(session_date: str, value: str) -> datetime:
        return datetime.fromisoformat(f"{session_date}T{value}:00+00:00")

    def check_in(
        self,
        *,
        participant_id: str,
        session_id: str,
        image: bytes,
        request_id: str,
    ) -> VerificationResult:
        session = self._repository.get_session(session_id)
        if session is None:
            raise SessionNotFoundError("Attendance session was not found")
        if session.status is not SessionStatus.ACTIVE:
            raise SessionClosedError("This attendance session is not active")
        now = datetime.now(UTC)
        if (
            not self._boundary(session.session_date, session.check_in_open)
            <= now
            <= self._boundary(session.session_date, session.check_in_close)
        ):
            raise SessionClosedError("This attendance session is outside its check-in window")

        try:
            result = self._verification.verify_identity(participant_id=participant_id, image=image)
        except PresenceGuardError as exc:
            self._repository.add_verification_attempt(
                participant_id=participant_id,
                session_id=session_id,
                face_detected=False,
                face_verification_result=VerificationStatus.REJECTED,
                liveness_result=LivenessStatus.UNAVAILABLE,
                final_result="failed",
                failure_reason=exc.code,
            )
            raise
        if result.status is not VerificationStatus.VERIFIED:
            self._repository.add_verification_attempt(
                participant_id=participant_id,
                session_id=session_id,
                face_detected=True,
                face_verification_result=result.status,
                liveness_result=LivenessStatus.UNAVAILABLE,
                final_result="rejected",
                failure_reason=result.reason,
            )
            return result

        liveness = self._liveness.check(image)
        if self._liveness_required and liveness.status is not LivenessStatus.PASSED:
            self._repository.add_verification_attempt(
                participant_id=participant_id,
                session_id=session_id,
                face_detected=True,
                face_verification_result=VerificationStatus.VERIFIED,
                liveness_result=liveness.status,
                final_result="rejected",
                failure_reason="liveness_required",
            )
            return VerificationResult(
                participant_id=participant_id,
                status=VerificationStatus.REJECTED,
                score=result.score,
                threshold=result.threshold,
                reason="liveness_required",
            )

        status = (
            AttendanceStatus.LATE
            if now >= self._boundary(session.session_date, session.late_threshold)
            else AttendanceStatus.PRESENT
        )
        record, created = self._repository.record_platform_attendance(
            participant_id=participant_id,
            session_id=session_id,
            status=status,
            verification_method=VerificationMethod.FACE,
            face_verification_score=result.score,
            liveness_result=liveness.status,
            check_in_timestamp=now,
            request_id=request_id,
        )
        self._repository.add_verification_attempt(
            participant_id=participant_id,
            session_id=session_id,
            face_detected=True,
            face_verification_result=VerificationStatus.VERIFIED,
            liveness_result=liveness.status,
            final_result="verified",
            failure_reason=None,
        )
        return VerificationResult(
            participant_id=participant_id,
            status=VerificationStatus.VERIFIED if created else VerificationStatus.DUPLICATE,
            score=result.score,
            threshold=result.threshold,
            event_id=record.attendance_id,
            occurred_at=record.check_in_timestamp,
            reason=("late" if created and status is AttendanceStatus.LATE else None)
            if created
            else "already_recorded",
        )
