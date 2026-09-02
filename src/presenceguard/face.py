"""Face extraction boundary and OpenCV YuNet/SFace implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import cv2 as cv
import numpy as np

from presenceguard.domain import FaceObservation
from presenceguard.errors import (
    InvalidImageError,
    LowQualityFaceError,
    ModelUnavailableError,
    MultipleFacesError,
    NoFaceError,
)


class FaceEngine(Protocol):
    dimension: int

    def extract(self, image_bytes: bytes) -> FaceObservation: ...


class OpenCVFaceEngine:
    dimension = 128

    def __init__(
        self,
        detector_path: Path,
        recognizer_path: Path,
        *,
        detection_threshold: float = 0.9,
        minimum_face_ratio: float = 0.12,
        minimum_sharpness: float = 25.0,
        minimum_brightness: float = 30.0,
        maximum_brightness: float = 225.0,
        maximum_pixels: int = 20_000_000,
    ):
        missing = [str(path) for path in (detector_path, recognizer_path) if not path.is_file()]
        if missing:
            raise ModelUnavailableError("Missing model file(s): " + ", ".join(missing))
        self._minimum_face_ratio = minimum_face_ratio
        self._minimum_sharpness = minimum_sharpness
        self._minimum_brightness = minimum_brightness
        self._maximum_brightness = maximum_brightness
        self._maximum_pixels = maximum_pixels
        self._detector = cv.FaceDetectorYN.create(
            str(detector_path), "", (320, 320), detection_threshold, 0.3, 5000
        )
        self._recognizer = cv.FaceRecognizerSF.create(str(recognizer_path), "")

    def extract(self, image_bytes: bytes) -> FaceObservation:
        if not image_bytes:
            raise InvalidImageError("Image is empty")
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv.imdecode(encoded, cv.IMREAD_COLOR)
        if image is None or image.ndim != 3 or image.shape[2] != 3:
            raise InvalidImageError("Image could not be decoded as RGB-compatible data")
        height, width = image.shape[:2]
        if height < 120 or width < 120:
            raise LowQualityFaceError("Image must be at least 120 by 120 pixels")
        if height * width > self._maximum_pixels:
            raise InvalidImageError("Decoded image exceeds the pixel safety limit")

        self._detector.setInputSize((width, height))
        _, faces = self._detector.detect(image)
        if faces is None or len(faces) == 0:
            raise NoFaceError("No face detected")
        if len(faces) != 1:
            raise MultipleFacesError("Exactly one face is required")
        face = faces[0]
        face_ratio = float(face[2] * face[3] / (width * height))
        if face_ratio < self._minimum_face_ratio:
            raise LowQualityFaceError("Face is too small in the frame")

        aligned = self._recognizer.alignCrop(image, face)
        gray = cv.cvtColor(aligned, cv.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        sharpness = float(cv.Laplacian(gray, cv.CV_64F).var())
        if not self._minimum_brightness <= brightness <= self._maximum_brightness:
            raise LowQualityFaceError("Face lighting is outside the accepted range")
        if sharpness < self._minimum_sharpness:
            raise LowQualityFaceError("Face image is too blurred")

        embedding = self._recognizer.feature(aligned).reshape(-1).astype(np.float32)
        norm = float(np.linalg.norm(embedding))
        if embedding.size != self.dimension or not np.isfinite(norm) or norm <= 0:
            raise InvalidImageError("Recognizer produced an invalid embedding")
        embedding /= norm
        return FaceObservation(
            embedding=embedding,
            detection_confidence=float(face[14]),
            brightness=brightness,
            sharpness=sharpness,
        )
