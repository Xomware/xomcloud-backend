"""Tests for lambdas.common.logger module."""

import json
import logging

from lambdas.common.logger import get_logger, JSONFormatter


class TestJSONFormatter:
    """Fix #16: Logging should be structured JSON."""

    def test_formats_as_json(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello world"
        assert parsed["line"] == 42
        assert "timestamp" in parsed

    def test_includes_exception_info(self) -> None:
        formatter = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="error happened",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestGetLogger:
    def test_returns_logger(self) -> None:
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_has_json_formatter(self) -> None:
        logger = get_logger("test_json_fmt")
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)
