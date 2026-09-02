"""Domain objects shared across interfaces and infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import numpy as np


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class UserRole(StrEnum):
    ADMIN = "admin"
    PARTICIPANT = "participant"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class EnrollmentStatus(StrEnum):
    NOT_ENROLLED = "not_enrolled"
    ENROLLED = "enrolled"
    NEEDS_REENROLLMENT = "needs_reenrollment"
    DISABLED = "disabled"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"
    MANUALLY_ADDED = "manually_added"


class VerificationMethod(StrEnum):
    FACE = "face"
    MANUAL_ADMIN = "manual_admin"
    INSTITUTIONAL = "institutional"
    FUTURE_ALTERNATIVE = "future_alternative"


class LivenessStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class FaceObservation:
    embedding: np.ndarray
    detection_confidence: float
    brightness: float
    sharpness: float


@dataclass(frozen=True)
class EnrollmentResult:
    participant_id: str
    accepted_samples: int
    rejected_samples: int
    threshold: float


@dataclass(frozen=True)
class ParticipantTemplate:
    participant_id: str
    display_name: str
    encrypted_template: bytes
    template_count: int
    threshold: float
    created_at: datetime
    consented_at: datetime


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    username: str
    email: str
    display_name: str
    role: UserRole
    status: AccountStatus
    password_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AttendanceSession:
    session_id: str
    title: str
    description: str
    course: str
    location: str
    session_date: str
    start_time: str
    end_time: str
    check_in_open: str
    check_in_close: str
    late_threshold: str
    status: SessionStatus
    created_by: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PlatformAttendanceRecord:
    attendance_id: str
    participant_id: str
    session_id: str
    status: AttendanceStatus
    check_in_timestamp: datetime | None
    verification_method: VerificationMethod
    face_verification_score: float | None
    liveness_result: LivenessStatus
    manually_adjusted: bool
    adjustment_reason: str | None
    adjusted_by: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class VerificationAttempt:
    attempt_id: str
    participant_id: str
    session_id: str | None
    occurred_at: datetime
    face_detected: bool
    face_verification_result: VerificationStatus
    liveness_result: LivenessStatus
    final_result: str
    failure_reason: str | None


@dataclass(frozen=True)
class AuditLog:
    audit_id: str
    actor_user_id: str | None
    action: str
    target_type: str
    target_id: str
    metadata: str
    reason: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class AttendanceRecord:
    event_id: str
    participant_id: str
    occurred_at: datetime
    similarity: float
    request_id: str


@dataclass(frozen=True)
class AttendanceWrite:
    record: AttendanceRecord | None
    created: bool
    idempotent_replay: bool
    blocked_by_window: bool


@dataclass(frozen=True)
class VerificationResult:
    participant_id: str
    status: VerificationStatus
    score: float
    threshold: float
    event_id: str | None = None
    occurred_at: datetime | None = None
    idempotent_replay: bool = False
    reason: str | None = None
