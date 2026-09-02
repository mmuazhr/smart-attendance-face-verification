"""Command-line entry point for local operation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn

from presenceguard.api import create_app
from presenceguard.config import Settings
from presenceguard.crypto import generate_template_key
from presenceguard.model_download import download_models
from presenceguard.observability import configure_logging
from presenceguard.repository import SQLiteRepository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="presenceguard")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate-key", help="Generate a template-encryption key")
    download = commands.add_parser("download-models", help="Download and verify OpenCV models")
    download.add_argument("--target", type=Path, default=Path("models"))
    download.add_argument("--force", action="store_true")
    commands.add_parser("init-db", help="Initialize the configured SQLite database")
    serve = commands.add_parser("serve", help="Run the local web application")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def app() -> None:
    args = _parser().parse_args()
    configure_logging()
    if args.command == "generate-key":
        print(generate_template_key())  # noqa: T201 - intentional CLI output
        return
    if args.command == "download-models":
        for path in download_models(args.target, force=args.force):
            print(path)  # noqa: T201 - intentional CLI output
        return

    settings = Settings()
    if args.command == "init-db":
        SQLiteRepository(settings.database_path).initialize()
        print(settings.database_path)  # noqa: T201 - intentional CLI output
        return
    if args.command == "serve":
        if args.host not in {"127.0.0.1", "localhost", "::1"}:
            print(  # noqa: T201 - explicit exposure warning
                "WARNING: binding beyond localhost exposes an unauthenticated enrollment surface."
            )
        application = create_app(settings)
        uvicorn.run(application, host=args.host, port=args.port, access_log=False)
        return
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    app()
