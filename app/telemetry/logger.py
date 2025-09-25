"""JSON logging formatter and helpers for telemetry."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from flask import g, has_request_context


class RequestContextFilter(logging.Filter):
    """Attach the current request id (if any) to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - contextual
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        else:
            record.request_id = "-"
        return True


class JsonFormatter(logging.Formatter):
    """Render log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = getattr(record, "request_id")
        for key in ("event", "user_id", "email", "ip", "status"):
            if hasattr(record, key):
                value = getattr(record, key)
                if value is not None:
                    payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(app) -> None:
    """Configure root/app logger to emit JSON structured logs."""

    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())
    root_logger.addHandler(handler)

    app.logger.handlers.clear()
    app.logger.propagate = True
    app.logger.setLevel(level)
