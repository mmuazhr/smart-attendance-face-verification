from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

import presenceguard.model_download as module
from presenceguard.model_download import ModelSpec, download_models


class FakeResponse(io.BytesIO):
    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


def test_download_is_checksummed_and_reuses_valid_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = b"model-bytes"
    spec = ModelSpec(
        filename="model.onnx",
        url="https://example.test/model.onnx",
        sha256=hashlib.sha256(payload).hexdigest(),
        license_name="MIT",
        license_url="https://example.test/license",
    )
    calls = 0

    def fake_open(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        calls += 1
        return FakeResponse(payload)

    monkeypatch.setattr(module, "MODELS", (spec,))
    monkeypatch.setattr(module.urllib.request, "urlopen", fake_open)

    assert download_models(tmp_path) == [tmp_path / "model.onnx"]
    assert download_models(tmp_path) == [tmp_path / "model.onnx"]
    assert calls == 1


def test_existing_corrupt_model_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spec = ModelSpec(
        filename="model.onnx",
        url="https://example.test/model.onnx",
        sha256=hashlib.sha256(b"expected").hexdigest(),
        license_name="MIT",
        license_url="https://example.test/license",
    )
    monkeypatch.setattr(module, "MODELS", (spec,))
    (tmp_path / "model.onnx").write_bytes(b"corrupt")

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        download_models(tmp_path)
