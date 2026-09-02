"""Password hashing and short-lived signed browser sessions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Passwords must contain at least 10 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    encode = base64.urlsafe_b64encode
    return f"{_ALGORITHM}${_ITERATIONS}${encode(salt).decode()}${encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def issue_session(user_id: str, role: str, secret: str, *, ttl_hours: int = 8) -> str:
    expires_at = datetime.now(UTC) + timedelta(hours=ttl_hours)
    payload = json.dumps(
        {"sub": user_id, "role": role, "exp": int(expires_at.timestamp())},
        separators=(",", ":"),
    ).encode()
    encoded = _encode(payload)
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_encode(signature)}"


def read_session(token: str | None, secret: str) -> dict[str, str] | None:
    if not token or not secret or token.count(".") != 1:
        return None
    encoded, signature = token.split(".", 1)
    expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
    try:
        supplied = _decode(signature)
        payload = json.loads(_decode(encoded))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    if not hmac.compare_digest(supplied, expected):
        return None
    if not isinstance(payload, dict) or int(payload.get("exp", 0)) < int(
        datetime.now(UTC).timestamp()
    ):
        return None
    subject = payload.get("sub")
    role = payload.get("role")
    if not isinstance(subject, str) or not isinstance(role, str):
        return None
    return {"sub": subject, "role": role}
