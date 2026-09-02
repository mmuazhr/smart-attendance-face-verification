"""Authenticated encryption for biometric templates."""

from __future__ import annotations

import base64
import os
import struct

import numpy as np
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from presenceguard.errors import InvalidRequestError, TemplateIntegrityError

_FORMAT_VERSION = 1
_NONCE_BYTES = 12
_HEADER = struct.Struct(">BHH")


def generate_template_key() -> str:
    """Return a URL-safe, environment-variable-ready 256-bit key."""

    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")


class TemplateCipher:
    def __init__(self, encoded_key: str):
        try:
            key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise InvalidRequestError("Template key must be URL-safe base64") from exc
        if len(key) != 32:
            raise InvalidRequestError("Template key must decode to exactly 32 bytes")
        self._cipher = AESGCM(key)

    @staticmethod
    def _aad(participant_id: str) -> bytes:
        return f"presenceguard:template:v1:{participant_id}".encode()

    def encrypt(self, participant_id: str, embeddings: np.ndarray) -> bytes:
        matrix = np.asarray(embeddings, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
            raise InvalidRequestError("Template must be a non-empty embedding matrix")
        if matrix.shape[0] > 100 or matrix.shape[1] > 4096:
            raise InvalidRequestError("Template dimensions exceed safety limits")
        header = _HEADER.pack(_FORMAT_VERSION, matrix.shape[0], matrix.shape[1])
        plaintext = header + matrix.astype(">f4", copy=False).tobytes(order="C")
        nonce = os.urandom(_NONCE_BYTES)
        return nonce + self._cipher.encrypt(nonce, plaintext, self._aad(participant_id))

    def decrypt(self, participant_id: str, token: bytes) -> np.ndarray:
        if len(token) <= _NONCE_BYTES:
            raise TemplateIntegrityError("Encrypted template is truncated")
        nonce, ciphertext = token[:_NONCE_BYTES], token[_NONCE_BYTES:]
        try:
            plaintext = self._cipher.decrypt(nonce, ciphertext, self._aad(participant_id))
        except InvalidTag as exc:
            raise TemplateIntegrityError("Encrypted template authentication failed") from exc
        if len(plaintext) < _HEADER.size:
            raise TemplateIntegrityError("Template payload is truncated")
        version, rows, columns = _HEADER.unpack(plaintext[: _HEADER.size])
        if version != _FORMAT_VERSION or rows == 0 or columns == 0:
            raise TemplateIntegrityError("Template header is invalid")
        expected = _HEADER.size + rows * columns * 4
        if len(plaintext) != expected:
            raise TemplateIntegrityError("Template payload length is invalid")
        matrix = np.frombuffer(plaintext[_HEADER.size :], dtype=">f4").astype(np.float32)
        return matrix.reshape(rows, columns)
