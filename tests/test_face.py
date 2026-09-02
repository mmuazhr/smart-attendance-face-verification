from __future__ import annotations

from pathlib import Path

import pytest

from presenceguard.errors import ModelUnavailableError
from presenceguard.face import OpenCVFaceEngine


def test_face_engine_fails_cleanly_when_models_are_missing(tmp_path: Path) -> None:
    with pytest.raises(ModelUnavailableError, match="Missing model"):
        OpenCVFaceEngine(tmp_path / "detector.onnx", tmp_path / "recognizer.onnx")
