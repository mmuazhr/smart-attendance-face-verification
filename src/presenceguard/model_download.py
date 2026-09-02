"""Checksummed acquisition of third-party OpenCV model files."""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelSpec:
    filename: str
    url: str
    sha256: str
    license_name: str
    license_url: str


MODELS = (
    ModelSpec(
        filename="face_detection_yunet_2023mar.onnx",
        url=(
            "https://github.com/opencv/opencv_zoo/raw/main/models/"
            "face_detection_yunet/face_detection_yunet_2023mar.onnx"
        ),
        sha256="8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        license_name="MIT",
        license_url=(
            "https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/LICENSE"
        ),
    ),
    ModelSpec(
        filename="face_recognition_sface_2021dec.onnx",
        url=(
            "https://github.com/opencv/opencv_zoo/raw/main/models/"
            "face_recognition_sface/face_recognition_sface_2021dec.onnx"
        ),
        sha256="0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        license_name="Apache-2.0",
        license_url=(
            "https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/LICENSE"
        ),
    ),
)


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_models(target: Path, *, force: bool = False) -> list[Path]:
    target.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for spec in MODELS:
        destination = target / spec.filename
        if destination.exists() and not force:
            if _checksum(destination) != spec.sha256:
                raise RuntimeError(f"Existing model checksum mismatch: {destination}")
            downloaded.append(destination)
            continue
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{spec.filename}.", dir=target)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            request = urllib.request.Request(  # noqa: S310 - fixed HTTPS allowlist above
                spec.url, headers={"User-Agent": "PresenceGuard/0.1 model downloader"}
            )
            with (
                urllib.request.urlopen(request, timeout=60) as response,  # nosec B310  # noqa: S310
                temporary.open("wb") as output,
            ):
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            actual = _checksum(temporary)
            if actual != spec.sha256:
                raise RuntimeError(
                    f"Checksum mismatch for {spec.filename}: expected {spec.sha256}, got {actual}"
                )
            temporary.replace(destination)
            downloaded.append(destination)
        finally:
            temporary.unlink(missing_ok=True)
    return downloaded
