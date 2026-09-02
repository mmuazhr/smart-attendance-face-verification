"""Runtime configuration sourced from explicit values or environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PRESENCEGUARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_path: Path = Path("data/private/presenceguard.db")
    yunet_model_path: Path = Path("models/face_detection_yunet_2023mar.onnx")
    sface_model_path: Path = Path("models/face_recognition_sface_2021dec.onnx")
    template_key: str = ""
    admin_token: str = ""
    match_threshold: float = Field(default=0.554712, ge=-1.0, le=1.0)
    detection_threshold: float = Field(default=0.9, ge=0.1, le=1.0)
    duplicate_window_seconds: int = Field(default=300, ge=0, le=86_400)
    minimum_enrollment_samples: int = Field(default=5, ge=3, le=50)
    maximum_enrollment_samples: int = Field(default=50, ge=3, le=50)
    maximum_upload_bytes: int = Field(default=5_000_000, ge=100_000, le=20_000_000)
    maximum_enrollment_request_bytes: int = Field(default=25_000_000, ge=1_000_000, le=100_000_000)
    minimum_face_ratio: float = Field(default=0.12, ge=0.01, le=1.0)
    minimum_sharpness: float = Field(default=25.0, ge=0.0)
    minimum_brightness: float = Field(default=30.0, ge=0.0, le=255.0)
    maximum_brightness: float = Field(default=225.0, ge=0.0, le=255.0)

    def require_template_key(self) -> str:
        if not self.template_key:
            raise ValueError(
                "PRESENCEGUARD_TEMPLATE_KEY is required; run `presenceguard generate-key`"
            )
        return self.template_key
