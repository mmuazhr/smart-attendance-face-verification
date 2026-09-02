"""FastAPI application for the authenticated PresenceGuard platform."""

from __future__ import annotations

import csv
import io
import logging
import secrets
import sqlite3
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, model_validator

from presenceguard.auth import issue_session, read_session, verify_password
from presenceguard.config import Settings
from presenceguard.crypto import TemplateCipher
from presenceguard.domain import (
    AccountStatus,
    AttendanceStatus,
    LivenessStatus,
    SessionStatus,
    UserRecord,
    UserRole,
    VerificationMethod,
    VerificationStatus,
)
from presenceguard.errors import (
    AdminAccessError,
    AuthenticationError,
    AuthorizationError,
    InvalidImageError,
    InvalidRequestError,
    ParticipantNotFoundError,
    PresenceGuardError,
    SessionNotFoundError,
)
from presenceguard.face import FaceEngine, OpenCVFaceEngine
from presenceguard.liveness import UnavailableLivenessProvider
from presenceguard.repository import SQLiteRepository
from presenceguard.services import AttendanceService, EnrollmentService, VerificationService


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(StrictModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class ParticipantCreateRequest(StrictModel):
    participant_id: str = Field(min_length=3, max_length=64)
    username: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=200)


class StatusRequest(StrictModel):
    status: AccountStatus


class SessionCreateRequest(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=500)
    course: str = Field(min_length=1, max_length=80)
    location: str = Field(default="", max_length=160)
    session_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    check_in_open: str = Field(pattern=r"^\d{2}:\d{2}$")
    check_in_close: str = Field(pattern=r"^\d{2}:\d{2}$")
    late_threshold: str = Field(pattern=r"^\d{2}:\d{2}$")

    @model_validator(mode="after")
    def validate_schedule(self) -> SessionCreateRequest:
        try:
            datetime.strptime(self.session_date, "%Y-%m-%d")
            start = datetime.strptime(self.start_time, "%H:%M")
            end = datetime.strptime(self.end_time, "%H:%M")
            check_in_open = datetime.strptime(self.check_in_open, "%H:%M")
            check_in_close = datetime.strptime(self.check_in_close, "%H:%M")
            late_threshold = datetime.strptime(self.late_threshold, "%H:%M")
        except ValueError as exc:
            raise ValueError("Session date and times must be valid") from exc
        if end <= start or check_in_close < check_in_open:
            raise ValueError("Session and check-in windows must move forward")
        if not check_in_open <= late_threshold <= check_in_close:
            raise ValueError("Late threshold must fall inside the check-in window")
        return self


class SessionStatusRequest(StrictModel):
    status: SessionStatus


class AttendanceCorrectionRequest(StrictModel):
    status: AttendanceStatus
    reason: str = Field(min_length=3, max_length=500)


class EnrollmentResponse(StrictModel):
    participant_id: str
    accepted_samples: int
    rejected_samples: int
    threshold: float


class VerificationResponse(StrictModel):
    participant_id: str
    status: VerificationStatus
    score: float
    threshold: float
    event_id: str | None
    occurred_at: str | None
    idempotent_replay: bool
    reason: str | None


class AttendanceResponse(StrictModel):
    event_id: str
    participant_id: str
    occurred_at: str
    similarity: float


class Runtime:
    def __init__(self, settings: Settings, face_engine: FaceEngine):
        self.settings = settings
        self.repository = SQLiteRepository(settings.database_path)
        self.repository.initialize()
        bootstrap_password = settings.admin_password or settings.admin_token
        if bootstrap_password:
            self.repository.ensure_bootstrap_admin(
                username=settings.admin_username, password=bootstrap_password
            )
        cipher = TemplateCipher(settings.require_template_key())
        self.enrollment = EnrollmentService(
            face_engine,
            cipher,
            self.repository,
            threshold=settings.match_threshold,
            minimum_samples=settings.minimum_enrollment_samples,
            maximum_samples=settings.maximum_enrollment_samples,
        )
        self.verification = VerificationService(
            face_engine,
            cipher,
            self.repository,
            duplicate_window_seconds=settings.duplicate_window_seconds,
        )
        self.attendance = AttendanceService(
            self.repository,
            self.verification,
            UnavailableLivenessProvider(),
            liveness_required=settings.liveness_required,
        )


def build_face_engine(settings: Settings) -> OpenCVFaceEngine:
    return OpenCVFaceEngine(
        settings.yunet_model_path,
        settings.sface_model_path,
        detection_threshold=settings.detection_threshold,
        minimum_face_ratio=settings.minimum_face_ratio,
        minimum_sharpness=settings.minimum_sharpness,
        minimum_brightness=settings.minimum_brightness,
        maximum_brightness=settings.maximum_brightness,
    )


async def _read_image(upload: UploadFile, limit: int) -> bytes:
    accepted = {"image/jpeg", "image/png", "image/webp"}
    if upload.content_type not in accepted:
        raise InvalidImageError("Only JPEG, PNG, and WebP images are accepted")
    payload = await upload.read(limit + 1)
    await upload.close()
    if len(payload) > limit:
        raise InvalidImageError("Image exceeds the upload limit")
    if not payload:
        raise InvalidImageError("Image is empty")
    return payload


def _user_payload(user: UserRecord, repository: SQLiteRepository) -> dict[str, Any]:
    participant = repository.get_participant(user.user_id)
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
        "status": user.status.value,
        "enrollment_status": (
            "disabled"
            if user.status is AccountStatus.DISABLED
            else "enrolled"
            if participant
            else "not_enrolled"
        ),
        "enrollment_samples": participant.template_count if participant else 0,
    }


def _session_payload(session: Any, repository: SQLiteRepository) -> dict[str, Any]:
    roster = repository.list_session_roster(session.session_id)
    records = [row for row in roster if row["attendance_id"]]
    present = sum(row["attendance_status"] in {"present", "late"} for row in records)
    late = sum(row["attendance_status"] == "late" for row in records)
    expected = sum(row["account_status"] == "active" for row in roster)
    return {
        "session_id": session.session_id,
        "title": session.title,
        "description": session.description,
        "course": session.course,
        "location": session.location,
        "session_date": session.session_date,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "check_in_open": session.check_in_open,
        "check_in_close": session.check_in_close,
        "late_threshold": session.late_threshold,
        "status": session.status.value,
        "created_by": session.created_by,
        "expected_participants": expected,
        "present_count": present,
        "late_count": late,
        "attendance_rate": round((present / expected) * 100, 1) if expected else 0.0,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def create_app(settings: Settings, *, face_engine: FaceEngine | None = None) -> FastAPI:
    runtime = Runtime(settings, face_engine or build_face_engine(settings))
    app = FastAPI(
        title="PresenceGuard",
        version="0.2.0",
        description=(
            "Authenticated, local, privacy-first attendance with research-grade boundaries."
        ),
    )
    app.state.runtime = runtime
    app.state.request_logger = logging.getLogger("presenceguard.request")

    @app.middleware("http")
    async def privacy_safe_request_log(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id.isascii() or not request_id.replace("-", "").isalnum():
            request_id = ""
        request_id = request_id[:64] or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        request.app.state.request_logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": route_path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    def require_admin_token(candidate: str | None) -> None:
        if (
            not settings.admin_token
            or not candidate
            or not secrets.compare_digest(settings.admin_token, candidate)
        ):
            raise AdminAccessError("A valid local admin token is required")

    def current_user(request: Request) -> UserRecord:
        claims = read_session(
            request.cookies.get("presenceguard_session"), settings.require_session_secret()
        )
        if claims is None:
            raise AuthenticationError("Sign in to continue")
        user = runtime.repository.get_user(claims["sub"])
        if user is None or user.status is AccountStatus.DISABLED:
            raise AuthenticationError("Your account is inactive or no longer exists")
        return user

    def admin_user(request: Request) -> UserRecord:
        user = current_user(request)
        if user.role is not UserRole.ADMIN:
            raise AuthorizationError("Administrator access is required")
        return user

    def admin_or_legacy(request: Request, token: str | None) -> UserRecord | None:
        if token and settings.admin_token and secrets.compare_digest(settings.admin_token, token):
            return None
        try:
            return admin_user(request)
        except AuthenticationError as exc:
            # Preserve the original local API's 403 contract for token-protected
            # compatibility routes; new account routes return 401 when unsigned.
            raise AdminAccessError("A valid local admin token is required") from exc

    @app.exception_handler(PresenceGuardError)
    async def handle_domain_error(_request: Request, exc: PresenceGuardError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index() -> HTMLResponse:
        return HTMLResponse((static_dir / "index.html").read_text(encoding="utf-8"))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "processing": "local",
            "image_retention": "none",
            "liveness": "unavailable",
        }

    @app.post("/api/v1/auth/login")
    async def login(payload: LoginRequest, response: Response) -> dict[str, Any]:
        user = runtime.repository.get_user_by_username(payload.username.strip())
        if (
            user is None
            or user.status is AccountStatus.DISABLED
            or not verify_password(payload.password, user.password_hash)
        ):
            raise AuthenticationError("Username or password was not recognised")
        token = issue_session(
            user.user_id,
            user.role.value,
            settings.require_session_secret(),
            ttl_hours=settings.session_ttl_hours,
        )
        response.set_cookie(
            "presenceguard_session",
            token,
            max_age=settings.session_ttl_hours * 60 * 60,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        runtime.repository.add_audit_log(
            actor_user_id=user.user_id,
            action="auth.login",
            target_type="user",
            target_id=user.user_id,
        )
        return {"user": _user_payload(user, runtime.repository)}

    @app.post("/api/v1/auth/logout")
    async def logout(request: Request, response: Response) -> dict[str, str]:
        user = current_user(request)
        response.delete_cookie("presenceguard_session")
        runtime.repository.add_audit_log(
            actor_user_id=user.user_id,
            action="auth.logout",
            target_type="user",
            target_id=user.user_id,
        )
        return {"status": "signed_out"}

    @app.get("/api/v1/auth/me")
    async def me(request: Request) -> dict[str, Any]:
        return {"user": _user_payload(current_user(request), runtime.repository)}

    @app.post("/api/v1/admin/participants")
    async def create_participant(
        payload: ParticipantCreateRequest, request: Request
    ) -> dict[str, Any]:
        actor = admin_user(request)
        try:
            user = runtime.repository.create_user(
                user_id=payload.participant_id,
                username=payload.username.strip(),
                email=payload.email.strip(),
                display_name=payload.display_name.strip(),
                role=UserRole.PARTICIPANT,
                password=payload.password,
            )
        except sqlite3.IntegrityError as exc:
            raise InvalidRequestError("Participant ID, username, or email already exists") from exc
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="user.created",
            target_type="user",
            target_id=user.user_id,
        )
        return {"user": _user_payload(user, runtime.repository)}

    @app.get("/api/v1/admin/participants")
    async def list_participants(request: Request) -> list[dict[str, Any]]:
        admin_user(request)
        result: list[dict[str, Any]] = []
        for user in runtime.repository.list_users(role=UserRole.PARTICIPANT):
            payload = _user_payload(user, runtime.repository)
            payload["attendance"] = runtime.repository.participant_summary(user.user_id)
            result.append(payload)
        return result

    @app.patch("/api/v1/admin/participants/{participant_id}/status")
    async def update_participant_status(
        participant_id: str, payload: StatusRequest, request: Request
    ) -> dict[str, Any]:
        actor = admin_user(request)
        if not runtime.repository.update_user_status(participant_id, payload.status):
            raise ParticipantNotFoundError("Participant account was not found")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="user.status_changed",
            target_type="user",
            target_id=participant_id,
            metadata=f'{{"status":"{payload.status.value}"}}',
        )
        user = runtime.repository.get_user(participant_id)
        if user is None:  # pragma: no cover
            raise ParticipantNotFoundError("Participant account was not found")
        return {"user": _user_payload(user, runtime.repository)}

    @app.post("/api/v1/participants/{participant_id}/enrollment", response_model=EnrollmentResponse)
    async def enroll(
        participant_id: str,
        display_name: Annotated[str, Form(min_length=1, max_length=100)],
        consent_confirmed: Annotated[bool, Form()],
        images: Annotated[list[UploadFile], File()],
        request: Request,
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    ) -> EnrollmentResponse:
        actor = admin_or_legacy(request, admin_token)
        if len(images) > settings.maximum_enrollment_samples:
            raise InvalidImageError("Too many enrollment images")
        payloads: list[bytes] = []
        total = 0
        for image in images:
            payload = await _read_image(image, settings.maximum_upload_bytes)
            total += len(payload)
            if total > settings.maximum_enrollment_request_bytes:
                raise InvalidImageError("Enrollment request exceeds the total upload limit")
            payloads.append(payload)
        result = runtime.enrollment.enroll(
            participant_id=participant_id,
            display_name=display_name,
            images=payloads,
            consent_confirmed=consent_confirmed,
        )
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id if actor else None,
            action="face.enrollment_completed",
            target_type="participant",
            target_id=participant_id,
            metadata=f'{{"accepted_samples":{result.accepted_samples}}}',
        )
        return EnrollmentResponse(**asdict(result))

    @app.post("/api/v1/me/enrollment", response_model=EnrollmentResponse)
    async def enroll_self(
        request: Request,
        images: Annotated[list[UploadFile], File()],
        display_name: Annotated[str | None, Form()] = None,
        consent_confirmed: Annotated[bool, Form()] = False,
    ) -> EnrollmentResponse:
        user = current_user(request)
        if user.role is not UserRole.PARTICIPANT:
            raise AuthorizationError("This self-enrollment route is for participants")
        if len(images) > settings.maximum_enrollment_samples:
            raise InvalidImageError("Too many enrollment images")
        payloads: list[bytes] = []
        total = 0
        for image in images:
            payload = await _read_image(image, settings.maximum_upload_bytes)
            total += len(payload)
            if total > settings.maximum_enrollment_request_bytes:
                raise InvalidImageError("Enrollment request exceeds the total upload limit")
            payloads.append(payload)
        result = runtime.enrollment.enroll(
            participant_id=user.user_id,
            display_name=(display_name or user.display_name),
            images=payloads,
            consent_confirmed=consent_confirmed,
        )
        runtime.repository.add_audit_log(
            actor_user_id=user.user_id,
            action="face.enrollment_completed",
            target_type="participant",
            target_id=user.user_id,
            metadata=f'{{"accepted_samples":{result.accepted_samples}}}',
        )
        return EnrollmentResponse(**asdict(result))

    @app.post(
        "/api/v1/participants/{participant_id}/verification",
        response_model=VerificationResponse,
    )
    async def verify(
        participant_id: str,
        image: Annotated[UploadFile, File()],
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=8, max_length=128)
        ],
    ) -> VerificationResponse:
        payload = await _read_image(image, settings.maximum_upload_bytes)
        result = runtime.verification.verify(
            participant_id=participant_id,
            image=payload,
            request_id=idempotency_key,
        )
        return VerificationResponse(
            participant_id=result.participant_id,
            status=result.status,
            score=result.score,
            threshold=result.threshold,
            event_id=result.event_id,
            occurred_at=result.occurred_at.isoformat() if result.occurred_at else None,
            idempotent_replay=result.idempotent_replay,
            reason=result.reason,
        )

    @app.delete("/api/v1/participants/{participant_id}", status_code=204)
    async def delete_participant(
        participant_id: str,
        request: Request,
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    ) -> None:
        actor = admin_or_legacy(request, admin_token)
        if not runtime.verification.delete_participant(participant_id):
            raise ParticipantNotFoundError("Participant is not enrolled")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id if actor else None,
            action="face.enrollment_deleted",
            target_type="participant",
            target_id=participant_id,
        )

    @app.get("/api/v1/attendance", response_model=list[AttendanceResponse])
    async def attendance(
        request: Request,
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
        participant_id: Annotated[str | None, Query(max_length=64)] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[AttendanceResponse]:
        admin_or_legacy(request, admin_token)
        return [
            AttendanceResponse(
                event_id=record.event_id,
                participant_id=record.participant_id,
                occurred_at=record.occurred_at.isoformat(),
                similarity=record.similarity,
            )
            for record in runtime.repository.list_attendance(
                participant_id=participant_id, limit=limit
            )
        ]

    @app.get("/api/v1/sessions")
    async def sessions(request: Request) -> list[dict[str, Any]]:
        user = current_user(request)
        all_sessions = runtime.repository.list_sessions()
        if user.role is UserRole.PARTICIPANT:
            all_sessions = [
                session
                for session in all_sessions
                if session.status in {SessionStatus.ACTIVE, SessionStatus.SCHEDULED}
            ]
        return [_session_payload(session, runtime.repository) for session in all_sessions]

    @app.post("/api/v1/admin/sessions")
    async def create_session(payload: SessionCreateRequest, request: Request) -> dict[str, Any]:
        actor = admin_user(request)
        try:
            session = runtime.repository.create_session(
                created_by=actor.user_id, **payload.model_dump()
            )
        except ValueError as exc:
            raise InvalidRequestError("Session date and times must be valid") from exc
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="session.created",
            target_type="session",
            target_id=session.session_id,
            metadata=f'{{"course":"{session.course}"}}',
        )
        return {"session": _session_payload(session, runtime.repository)}

    @app.patch("/api/v1/admin/sessions/{session_id}/status")
    async def update_session_status(
        session_id: str, payload: SessionStatusRequest, request: Request
    ) -> dict[str, Any]:
        actor = admin_user(request)
        session = runtime.repository.update_session_status(session_id, payload.status)
        if session is None:
            raise SessionNotFoundError("Attendance session was not found")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="session.status_changed",
            target_type="session",
            target_id=session_id,
            metadata=f'{{"status":"{payload.status.value}"}}',
        )
        return {"session": _session_payload(session, runtime.repository)}

    @app.patch("/api/v1/admin/sessions/{session_id}")
    async def edit_session(
        session_id: str, payload: SessionCreateRequest, request: Request
    ) -> dict[str, Any]:
        actor = admin_user(request)
        session = runtime.repository.update_session_details(session_id, payload.model_dump())
        if session is None:
            raise SessionNotFoundError("Attendance session was not found")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="session.updated",
            target_type="session",
            target_id=session_id,
        )
        return {"session": _session_payload(session, runtime.repository)}

    @app.get("/api/v1/admin/sessions/{session_id}/roster")
    async def session_roster(session_id: str, request: Request) -> dict[str, Any]:
        admin_user(request)
        session = runtime.repository.get_session(session_id)
        if session is None:
            raise SessionNotFoundError("Attendance session was not found")
        roster = runtime.repository.list_session_roster(session_id)
        for row in roster:
            if not row["attendance_id"]:
                row["attendance_status"] = "absent"
        return {"session": _session_payload(session, runtime.repository), "roster": roster}

    @app.post("/api/v1/sessions/{session_id}/check-in", response_model=VerificationResponse)
    async def session_check_in(
        session_id: str,
        image: Annotated[UploadFile, File()],
        request: Request,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> VerificationResponse:
        user = current_user(request)
        if user.role is not UserRole.PARTICIPANT:
            raise AuthorizationError("Only participant accounts can check in through this route")
        payload = await _read_image(image, settings.maximum_upload_bytes)
        result = runtime.attendance.check_in(
            participant_id=user.user_id,
            session_id=session_id,
            image=payload,
            request_id=idempotency_key or str(uuid.uuid4()),
        )
        return VerificationResponse(
            participant_id=result.participant_id,
            status=result.status,
            score=result.score,
            threshold=result.threshold,
            event_id=result.event_id,
            occurred_at=result.occurred_at.isoformat() if result.occurred_at else None,
            idempotent_replay=result.idempotent_replay,
            reason=result.reason,
        )

    @app.get("/api/v1/attendance/history")
    async def attendance_history(
        request: Request,
        participant_id: Annotated[str | None, Query(max_length=64)] = None,
    ) -> list[dict[str, Any]]:
        user = current_user(request)
        if user.role is not UserRole.ADMIN:
            participant_id = user.user_id
        records = runtime.repository.list_platform_attendance(participant_id=participant_id)
        result = []
        for record in records:
            session = runtime.repository.get_session(record.session_id)
            result.append(
                {
                    "attendance_id": record.attendance_id,
                    "participant_id": record.participant_id,
                    "session_id": record.session_id,
                    "session_title": session.title if session else "Unknown session",
                    "course": session.course if session else "",
                    "session_date": session.session_date if session else "",
                    "status": record.status.value,
                    "check_in_timestamp": record.check_in_timestamp.isoformat()
                    if record.check_in_timestamp
                    else None,
                    "verification_method": record.verification_method.value,
                    "liveness_result": record.liveness_result.value,
                    "manually_adjusted": record.manually_adjusted,
                    "adjustment_reason": record.adjustment_reason,
                }
            )
        return result

    @app.patch("/api/v1/admin/attendance/{attendance_id}")
    async def correct_attendance(
        attendance_id: str,
        payload: AttendanceCorrectionRequest,
        request: Request,
    ) -> dict[str, Any]:
        actor = admin_user(request)
        record = runtime.repository.correct_attendance(
            attendance_id=attendance_id,
            status=payload.status,
            reason=payload.reason.strip(),
            adjusted_by=actor.user_id,
        )
        if record is None:
            raise InvalidRequestError("Attendance record was not found")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="attendance.corrected",
            target_type="attendance",
            target_id=attendance_id,
            reason=payload.reason.strip(),
            metadata=f'{{"status":"{payload.status.value}"}}',
        )
        return {"attendance": asdict(record)}

    @app.post("/api/v1/admin/sessions/{session_id}/attendance/{participant_id}")
    async def manually_set_attendance(
        session_id: str,
        participant_id: str,
        payload: AttendanceCorrectionRequest,
        request: Request,
    ) -> dict[str, Any]:
        actor = admin_user(request)
        if runtime.repository.get_session(session_id) is None:
            raise SessionNotFoundError("Attendance session was not found")
        if runtime.repository.get_user(participant_id) is None:
            raise ParticipantNotFoundError("Participant account was not found")
        existing = runtime.repository.list_platform_attendance(
            participant_id=participant_id, session_id=session_id
        )
        if existing:
            record = runtime.repository.correct_attendance(
                attendance_id=existing[0].attendance_id,
                status=payload.status,
                reason=payload.reason.strip(),
                adjusted_by=actor.user_id,
            )
        else:
            record, _ = runtime.repository.record_platform_attendance(
                participant_id=participant_id,
                session_id=session_id,
                status=payload.status,
                verification_method=VerificationMethod.MANUAL_ADMIN,
                face_verification_score=None,
                liveness_result=LivenessStatus.UNAVAILABLE,
                check_in_timestamp=None,
                request_id=str(uuid.uuid4()),
            )
            record = runtime.repository.correct_attendance(
                attendance_id=record.attendance_id,
                status=payload.status,
                reason=payload.reason.strip(),
                adjusted_by=actor.user_id,
            )
        if record is None:  # pragma: no cover
            raise InvalidRequestError("Attendance record could not be saved")
        runtime.repository.add_audit_log(
            actor_user_id=actor.user_id,
            action="attendance.corrected",
            target_type="attendance",
            target_id=record.attendance_id,
            reason=payload.reason.strip(),
            metadata=(
                f'{{"participant_id":"{participant_id}","session_id":"{session_id}",'
                f'"status":"{payload.status.value}"}}'
            ),
        )
        return {"attendance": asdict(record)}

    @app.get("/api/v1/admin/dashboard")
    async def admin_dashboard(request: Request) -> dict[str, Any]:
        admin_user(request)
        return {
            "metrics": runtime.repository.dashboard_summary(),
            "sessions": [
                _session_payload(session, runtime.repository)
                for session in runtime.repository.list_sessions()
                if session.status in {SessionStatus.ACTIVE, SessionStatus.SCHEDULED}
            ][:6],
            "failed_attempts": runtime.repository.list_verification_attempts(
                limit=12, failures_only=True
            ),
        }

    @app.get("/api/v1/admin/audit-logs")
    async def audit_logs(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[dict[str, Any]]:
        admin_user(request)
        return [
            {
                "audit_id": entry.audit_id,
                "actor_user_id": entry.actor_user_id,
                "action": entry.action,
                "target_type": entry.target_type,
                "target_id": entry.target_id,
                "metadata": entry.metadata,
                "reason": entry.reason,
                "occurred_at": entry.occurred_at.isoformat(),
            }
            for entry in runtime.repository.list_audit_logs(limit=limit)
        ]

    @app.get("/api/v1/admin/reports/attendance.csv")
    async def attendance_report(request: Request) -> Response:
        admin_user(request)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "attendance_id",
                "participant_id",
                "session_id",
                "status",
                "check_in_timestamp",
                "method",
            ]
        )
        for record in runtime.repository.list_platform_attendance():
            writer.writerow(
                [
                    record.attendance_id,
                    record.participant_id,
                    record.session_id,
                    record.status.value,
                    record.check_in_timestamp.isoformat() if record.check_in_timestamp else "",
                    record.verification_method.value,
                ]
            )
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=presenceguard-attendance.csv"},
        )

    @app.get("/{path:path}", response_class=HTMLResponse, include_in_schema=False)
    async def client_routes(path: str) -> HTMLResponse:
        if path.startswith("api/") or path.startswith("static/"):
            raise ParticipantNotFoundError("Route not found")
        return HTMLResponse((static_dir / "index.html").read_text(encoding="utf-8"))

    return app


def create_configured_app() -> FastAPI:
    return create_app(Settings())
