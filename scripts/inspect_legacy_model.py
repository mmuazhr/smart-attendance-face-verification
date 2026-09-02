#!/usr/bin/env python3
"""Inspect a legacy Keras HDF5 model without importing TensorFlow.

The source model is private and deliberately excluded from Git. This command writes
only architecture/configuration metadata that is safe to review and reproduce.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py


def _decode(value: Any) -> Any:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dataset_metadata(dataset: h5py.Dataset) -> dict[str, Any]:
    return {
        "shape": list(dataset.shape),
        "dtype": str(dataset.dtype),
        "parameters": int(dataset.size),
    }


def _walk(group: h5py.Group) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, item in group.items():
        if isinstance(item, h5py.Dataset):
            result[name] = _dataset_metadata(item)
        else:
            result[name] = {
                "attributes": {key: _decode(value) for key, value in item.attrs.items()},
                "children": _walk(item),
            }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    model_path = args.model.resolve()
    with h5py.File(model_path, "r") as model:
        payload = {
            "file": {
                "name": model_path.name,
                "bytes": model_path.stat().st_size,
                "sha256": _sha256(model_path),
            },
            "attributes": {key: _decode(value) for key, value in model.attrs.items()},
            "contents": _walk(model),
        }

    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
