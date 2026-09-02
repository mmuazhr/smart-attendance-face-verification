"""Audit a private face-image dataset without exposing image content.

The command reports counts, dimensions, encodings, byte sizes, unreadable files,
and exact duplicate groups. It emits only paths and aggregate metadata so the
result can be reviewed without copying biometric images into Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(root: Path) -> dict[str, Any]:
    class_counts: Counter[str] = Counter()
    class_bytes: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    formats: Counter[str] = Counter()
    modes: Counter[str] = Counter()
    hashes: defaultdict[str, list[str]] = defaultdict(list)
    unreadable: list[dict[str, str]] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root)
        class_name = relative.parts[0] if len(relative.parts) > 1 else "."
        class_counts[class_name] += 1
        class_bytes[class_name] += path.stat().st_size
        hashes[sha256(path)].append(relative.as_posix())

        try:
            with Image.open(path) as image:
                dimensions[f"{image.width}x{image.height}"] += 1
                formats[str(image.format)] += 1
                modes[image.mode] += 1
                image.verify()
        except Exception as error:  # pragma: no cover - depends on source files
            unreadable.append({"path": relative.as_posix(), "error": str(error)})

    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    cross_class_duplicates = [
        paths for paths in duplicate_groups if len({path.split("/", 1)[0] for path in paths}) > 1
    ]

    return {
        "root": str(root.resolve()),
        "total_files": sum(class_counts.values()),
        "class_counts": dict(sorted(class_counts.items())),
        "class_bytes": dict(sorted(class_bytes.items())),
        "dimensions": dict(dimensions.most_common()),
        "formats": dict(formats.most_common()),
        "modes": dict(modes.most_common()),
        "unreadable": unreadable,
        "exact_duplicate_group_count": len(duplicate_groups),
        "exact_duplicate_extra_file_count": sum(len(paths) - 1 for paths in duplicate_groups),
        "cross_class_duplicate_group_count": len(cross_class_duplicates),
        "exact_duplicate_groups": duplicate_groups,
        "cross_class_duplicate_groups": cross_class_duplicates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Dataset directory to audit")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; stdout is always populated",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = audit(args.root)
    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
