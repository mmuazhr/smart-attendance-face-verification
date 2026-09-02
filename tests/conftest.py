from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from presenceguard.domain import FaceObservation
from presenceguard.errors import NoFaceError
from presenceguard.repository import SQLiteRepository


class FakeFaceEngine:
    dimension = 3

    def extract(self, image_bytes: bytes) -> FaceObservation:
        if image_bytes == b"bad":
            raise NoFaceError("No face detected")
        vectors = {
            b"front": np.asarray([1.0, 0.0, 0.0], dtype=np.float32),
            b"angle": np.asarray([0.98, 0.2, 0.0], dtype=np.float32),
            b"other": np.asarray([0.0, 1.0, 0.0], dtype=np.float32),
        }
        vector = vectors.get(image_bytes, vectors[b"front"]).copy()
        vector /= np.linalg.norm(vector)
        return FaceObservation(
            embedding=vector,
            detection_confidence=0.99,
            brightness=120.0,
            sharpness=100.0,
        )


@pytest.fixture
def fake_face_engine() -> FakeFaceEngine:
    return FakeFaceEngine()


@pytest.fixture
def repository(tmp_path: Path) -> SQLiteRepository:
    instance = SQLiteRepository(tmp_path / "presenceguard.db")
    instance.initialize()
    return instance
