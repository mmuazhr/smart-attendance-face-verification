#!/usr/bin/env python3
"""Convert a notebook into reviewable, deterministic text and metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text(value: Any) -> str:
    if isinstance(value, list):
        return "".join(str(part) for part in value)
    return str(value or "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--source-output", type=Path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()

    raw = args.notebook.read_bytes()
    notebook = json.loads(raw)
    source_parts: list[str] = []
    output_types: dict[str, int] = {}
    execution_counts: list[int] = []

    for index, cell in enumerate(notebook.get("cells", []), start=1):
        source = _text(cell.get("source"))
        source_parts.append(f"# %% [{cell.get('cell_type', 'unknown')}] cell {index}\n{source.rstrip()}\n")
        count = cell.get("execution_count")
        if isinstance(count, int):
            execution_counts.append(count)
        for output in cell.get("outputs", []):
            kind = str(output.get("output_type", "unknown"))
            output_types[kind] = output_types.get(kind, 0) + 1

    source_text = "\n".join(source_parts).rstrip() + "\n"
    summary = {
        "file": args.notebook.name,
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "nbformat": notebook.get("nbformat"),
        "nbformat_minor": notebook.get("nbformat_minor"),
        "kernel": notebook.get("metadata", {}).get("kernelspec", {}),
        "language": notebook.get("metadata", {}).get("language_info", {}),
        "cells": len(notebook.get("cells", [])),
        "code_cells": sum(cell.get("cell_type") == "code" for cell in notebook.get("cells", [])),
        "markdown_cells": sum(cell.get("cell_type") == "markdown" for cell in notebook.get("cells", [])),
        "executed_code_cells": len(execution_counts),
        "maximum_execution_count": max(execution_counts, default=None),
        "output_types": output_types,
        "source_sha256": _sha256(source_text.encode("utf-8")),
    }

    if args.source_output:
        args.source_output.parent.mkdir(parents=True, exist_ok=True)
        args.source_output.write_text(source_text, encoding="utf-8")
    else:
        print(source_text)

    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.summary_output:
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
