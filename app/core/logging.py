"""Logging helpers para request-id y configuración básica."""

from __future__ import annotations

import logging
import uuid

from flask import Flask, g, request


def _ensure_request_id() -> None:
    if getattr(g, "request_id", None):
        return
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


def _attach_request_id(response):  # type: ignore[override]
    response.headers.setdefault("X-Request-ID", getattr(g, "request_id", "-"))
    return response


def init_logging(app: Flask) -> None:
    """Configura logging básico y garantiza un request id."""

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=logging.INFO)

    app.before_request(_ensure_request_id)
    app.after_request(_attach_request_id)

