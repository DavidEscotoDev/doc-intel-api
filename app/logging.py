# app/logging.py
"""Structured logging configuration with structlog."""

import sys
import logging
from typing import Any
import structlog
from structlog.types import EventDict, Processor


def add_service_info(_: Any, __: Any, event_dict: EventDict) -> EventDict:
    """Add service metadata to all log entries."""
    event_dict["service"] = "document-intelligence-api"
    event_dict["version"] = "1.0.0"
    return event_dict


def drop_color_message_key(_: Any, __: Any, event_dict: EventDict) -> EventDict:
    """Remove color_message key added by structlog.dev.ConsoleRenderer."""
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structlog for structured JSON logging."""

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_service_info,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        drop_color_message_key,
    ]

    if json_logs:
        # Production: JSON output for log aggregation
        renderer: Processor = structlog.processors.JSONRenderer()
        processors = shared_processors + [renderer]
    else:
        # Development: Human-readable console output
        console_renderer: Processor = structlog.dev.ConsoleRenderer(colors=True)
        processors = shared_processors + [
            structlog.processors.ExceptionPrettyPrinter(),
            console_renderer,
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]