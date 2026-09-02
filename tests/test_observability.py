from __future__ import annotations

import json
import logging

import presenceguard.observability as observability
from presenceguard.observability import JsonFormatter


def test_json_formatter_allowlists_request_fields_and_redacts_sensitive_extras() -> None:
    record = logging.LogRecord(
        name="presenceguard.request",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-1"
    record.method = "POST"
    record.route = "/api/v1/participants/{participant_id}/verification"
    record.status_code = 200
    record.duration_ms = 12.34
    record.participant_id = "student-001"
    record.embedding = "private-vector"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "http_request"
    assert payload["request_id"] == "request-1"
    assert payload["route"].endswith("{participant_id}/verification")
    assert payload["duration_ms"] == 12.34
    assert "participant_id" not in payload
    assert "embedding" not in payload


def test_json_formatter_records_exception_type_without_exception_details() -> None:
    try:
        raise ValueError("secret payload should not be logged")
    except ValueError:
        record = logging.LogRecord(
            name="presenceguard",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="request_failed",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["exception"] == "ValueError"
    assert "secret payload" not in json.dumps(payload)


def test_configure_logging_adds_and_formats_a_root_handler() -> None:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    try:
        root.handlers.clear()
        observability.configure_logging(logging.DEBUG)

        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JsonFormatter)
        assert root.level == logging.DEBUG
    finally:
        root.handlers.clear()
        root.handlers.extend(original_handlers)
        root.setLevel(original_level)
