"""
Structured logging configuration for IAM Policy Classifier.

Provides setup_logging() which configures the root logger once at startup:
  - production / staging  →  JSON lines (one compact JSON object per record)
  - development           →  human-readable text (original basicConfig format)

JSON records always include: timestamp, level, logger, message.
Any extra={} fields passed to logger.info/error/… are merged in automatically.
Exception info (exc_info) is serialised to a top-level "exception" key.
"""

import json
import logging
import logging.handlers
import socket
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# JSON Formatter
# ---------------------------------------------------------------------------

# Standard LogRecord attributes that should NOT be treated as "extra" fields.
_STANDARD_ATTRS: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    """
    Emit one JSON object per log record.

    Fields emitted:
        timestamp  — ISO-8601 UTC timestamp
        level      — log level name (INFO, ERROR, …)
        logger     — logger name (e.g. src.api.routes.classify)
        message    — formatted message string
        exception  — formatted traceback (only when exc_info is present)
        <extras>   — any key/value pairs passed via extra={} in the log call
    """

    def format(self, record: logging.LogRecord) -> str:
        # Ensure record.message is populated (mirrors what Formatter.format does)
        record.message = record.getMessage()

        data: dict = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }

        # Merge extra fields (anything injected via extra={} in the log call)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                data[key] = value

        # Serialise exception info if present
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)

        return json.dumps(data, default=str)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def setup_logging(
    level: Optional[str] = None,
    use_json: Optional[bool] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure the root logger exactly once.

    Parameters default to values from settings when not provided explicitly,
    which makes this function easy to unit-test with overrides.

    Args:
        level:    Log level string ("DEBUG", "INFO", …). Defaults to settings.LOG_LEVEL.
        use_json: Force JSON (True) or text (False) output. When None, JSON is
                  enabled automatically for production and staging environments.
        log_file: Optional path for a rotating file handler in addition to stderr.
    """
    # Import here (not at module level) to avoid import-time side effects and
    # to prevent circular imports when logging.py is imported early.
    from src.config import settings as _settings

    effective_level = level or _settings.LOG_LEVEL
    numeric_level = getattr(logging, effective_level, logging.INFO)

    # Decide format: JSON for non-development, or when explicitly requested.
    if use_json is None:
        json_mode = not _settings.is_development() or _settings.LOG_JSON
    else:
        json_mode = use_json

    # Build the formatter
    if json_mode:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt=_settings.LOG_FORMAT,
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    # Configure the root logger: remove any existing handlers first so that
    # repeated calls (e.g. during tests) don't stack duplicate handlers.
    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()

    # Stream handler (stderr)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Optional rotating file handler
    effective_log_file = log_file or _settings.LOG_FILE
    if effective_log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            effective_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # Suppress noisy third-party loggers in production
    if not _settings.is_development():
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Emit a startup message so the first log line confirms the format
    startup_log = logging.getLogger(__name__)
    startup_log.info(
        "Logging configured",
        extra={
            "format": "json" if json_mode else "text",
            "level": effective_level,
            "log_file": effective_log_file,
            "log_group": _settings.LOG_GROUP_NAME,
            "log_stream": _resolve_stream_name(_settings.LOG_STREAM_NAME, _settings.ENVIRONMENT),
        },
    )


def _resolve_stream_name(template: str, environment: str) -> str:
    """Expand {environment} and {hostname} placeholders in the stream name template."""
    return template.format(
        environment=environment,
        hostname=socket.gethostname(),
    )
