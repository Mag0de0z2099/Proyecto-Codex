"""Configuración centralizada de logging para la aplicación."""

from __future__ import annotations

import logging
from flask import g, has_request_context


class RequestIdFilter(logging.Filter):
    """Adjunta el `request_id` actual (si existe) a cada registro."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - acceso contextual
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        else:
            record.request_id = "-"
        return True


def setup_logging(app) -> None:
    """Inicializa el logger principal de Flask usando el filtro de request id."""

    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    fmt = "%(asctime)s %(levelname)s %(request_id)s %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
