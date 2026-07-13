# tests/test_logging.py
"""Tests for logging module."""

import logging
from app.logging import setup_logging, get_logger, add_service_info, drop_color_message_key


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_json(self) -> None:
        setup_logging(log_level="DEBUG", json_logs=True)
        # Should not raise

    def test_setup_logging_console(self) -> None:
        setup_logging(log_level="INFO", json_logs=False)
        # Should not raise

    def test_log_levels(self) -> None:
        setup_logging(log_level="WARNING", json_logs=False)
        # uvicorn.access should be WARNING
        assert logging.getLogger("uvicorn.access").level == logging.WARNING
        assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING


class TestGetLogger:
    """Test get_logger function."""

    def test_returns_bound_logger(self) -> None:
        logger = get_logger("test.module")
        # structlog.get_logger returns a BoundLoggerLazyProxy that becomes BoundLogger on first use
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        # Call a method to trigger resolution
        logger.info("test")
        assert hasattr(logger, "_logger")

    def test_different_names(self) -> None:
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2


class TestAddServiceInfo:
    """Test add_service_info processor."""

    def test_adds_service_info(self) -> None:
        event_dict = {"message": "test"}
        result = add_service_info(None, None, event_dict)
        assert result["service"] == "document-intelligence-api"
        assert result["version"] == "1.0.0"
        assert result["message"] == "test"


class TestDropColorMessageKey:
    """Test drop_color_message_key processor."""

    def test_removes_color_message(self) -> None:
        event_dict = {"message": "test", "color_message": "colored"}
        result = drop_color_message_key(None, None, event_dict)
        assert "color_message" not in result
        assert result["message"] == "test"

    def test_no_color_message(self) -> None:
        event_dict = {"message": "test"}
        result = drop_color_message_key(None, None, event_dict)
        assert result == event_dict