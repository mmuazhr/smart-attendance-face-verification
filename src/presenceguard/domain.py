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
