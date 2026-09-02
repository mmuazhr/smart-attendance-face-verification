from __future__ import annotations

import numpy as np
import pytest

from presenceguard.crypto import TemplateCipher, generate_template_key
from presenceguard.errors import InvalidRequestError, TemplateIntegrityError


def test_template_round_trip_and_random_nonce() -> None:
    cipher = TemplateCipher(generate_template_key())
    template = np.asarray([[1.0, 0.0, 0.5], [0.2, 0.3, 0.4]], dtype=np.float32)

    first = cipher.encrypt("student-001", template)
    second = cipher.encrypt("student-001", template)

    assert first != second
    np.testing.assert_allclose(cipher.decrypt("student-001", first), template)


def test_template_is_bound_to_participant_and_detects_tampering() -> None:
    cipher = TemplateCipher(generate_template_key())
    token = cipher.encrypt("student-001", np.ones((2, 3), dtype=np.float32))

    with pytest.raises(TemplateIntegrityError):
        cipher.decrypt("student-002", token)

    tampered = bytearray(token)
    tampered[-1] ^= 1
    with pytest.raises(TemplateIntegrityError):
        cipher.decrypt("student-001", bytes(tampered))


def test_invalid_template_key_is_rejected() -> None:
    with pytest.raises(InvalidRequestError):
        TemplateCipher("not-a-256-bit-key")
