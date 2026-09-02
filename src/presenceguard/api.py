"""Local FastAPI interface for enrollment and attendance verification."""

from __future__ import annotations

import logging
import secrets
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from presenceguard.config import Settings
from presenceguard.crypto import TemplateCipher
from presenceguard.domain import VerificationStatus
from presenceguard.errors import (
    AdminAccessError,
    InvalidImageError,
    ParticipantNotFoundError,
    PresenceGuardError,
)
from presenceguard.face import FaceEngine, OpenCVFaceEngine
from presenceguard.repository import SQLiteRepository
from presenceguard.services import EnrollmentService, VerificationService


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


def create_app(settings: Settings, *, face_engine: FaceEngine | None = None) -> FastAPI:
    runtime = Runtime(settings, face_engine or build_face_engine(settings))
    app = FastAPI(
        title="PresenceGuard",
        version="0.1.0",
        description="Local, privacy-first face verification for attendance research.",
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
        return {"status": "ok", "processing": "local", "image_retention": "none"}

    @app.post("/api/v1/participants/{participant_id}/enrollment", response_model=EnrollmentResponse)
    async def enroll(
        participant_id: str,
        display_name: Annotated[str, Form(min_length=1, max_length=100)],
        consent_confirmed: Annotated[bool, Form()],
        images: Annotated[list[UploadFile], File()],
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    ) -> EnrollmentResponse:
        require_admin_token(admin_token)
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
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
    ) -> None:
        require_admin_token(admin_token)
        if not runtime.verification.delete_participant(participant_id):
            raise ParticipantNotFoundError("Participant is not enrolled")

    @app.get("/api/v1/attendance", response_model=list[AttendanceResponse])
    async def attendance(
        admin_token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
        participant_id: Annotated[str | None, Query(max_length=64)] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> list[AttendanceResponse]:
        require_admin_token(admin_token)
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

    return app


def create_configured_app() -> FastAPI:
    return create_app(Settings())
