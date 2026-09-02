"""Typed errors exposed consistently by services and the HTTP API."""

from __future__ import annotations


class PresenceGuardError(Exception):
    code = "presenceguard_error"
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidRequestError(PresenceGuardError):
    code = "invalid_request"
    status_code = 422


class ConsentRequiredError(InvalidRequestError):
    code = "consent_required"


class InvalidImageError(PresenceGuardError):
    code = "invalid_image"


class NoFaceError(PresenceGuardError):
    code = "no_face"


class MultipleFacesError(PresenceGuardError):
    code = "multiple_faces"


class LowQualityFaceError(PresenceGuardError):
    code = "low_quality_face"


class ParticipantNotFoundError(PresenceGuardError):
    code = "participant_not_found"
    status_code = 404


class ModelUnavailableError(PresenceGuardError):
    code = "model_unavailable"
    status_code = 503


class TemplateIntegrityError(PresenceGuardError):
    code = "template_integrity_error"
    status_code = 500


class AdminAccessError(PresenceGuardError):
    code = "admin_access_denied"
    status_code = 403


class AuthenticationError(PresenceGuardError):
    code = "authentication_required"
    status_code = 401


class AuthorizationError(PresenceGuardError):
    code = "not_authorized"
    status_code = 403


class SessionNotFoundError(PresenceGuardError):
    code = "session_not_found"
    status_code = 404


class SessionClosedError(PresenceGuardError):
    code = "session_unavailable"
    status_code = 409


class AttendanceAlreadyRecordedError(PresenceGuardError):
    code = "attendance_already_recorded"
    status_code = 409
