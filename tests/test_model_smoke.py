from __future__ import annotations

from pathlib import Path

import pytest

from presenceguard.face import OpenCVFaceEngine


@pytest.mark.private_model
def test_private_opencv_model_smoke() -> None:
    detector = Path(".private/models/face_detection_yunet_2023mar.onnx")
    recognizer = Path(".private/models/face_recognition_sface_2021dec.onnx")
    images = Path(".private/source/extracted/data-archive/data/anchor")
    if not detector.is_file() or not recognizer.is_file() or not images.is_dir():
        pytest.skip("Private model/data artifacts are not installed")
    image = next(images.glob("*.jpg"))
    engine = OpenCVFaceEngine(detector, recognizer, minimum_sharpness=0)

    observation = engine.extract(image.read_bytes())

    assert observation.embedding.shape == (128,)
    assert abs(float((observation.embedding**2).sum()) - 1.0) < 1e-5
