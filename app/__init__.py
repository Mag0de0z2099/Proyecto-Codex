"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

from flask import Flask, g, has_request_context, request
from werkzeug.exceptions import HTTPException

from .blueprints.admin import bp_admin
from .blueprints.api.v1 import bp_api_v1
from .blueprints.auth import bp_auth
from .blueprints.ping import bp_ping
from .blueprints.web import bp_web
from .routes.public import public_bp
from .config import get_config
from .db import db
from .extensions import csrf, init_auth_extensions, limiter
from .cli import register_cli
from .migrate_ext import init_migrations
from .security_headers import set_security_headers
from .storage import ensure_dirs


class RequestIDFilter(logging.Filter):
    """Attach the current request id (if any) to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - filter logic
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        else:
            record.request_id = "-"
        return True


def configure_logging(app: Flask) -> None:
    """Configure structured logging to stdout for the application."""

    log_level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = []
    if gunicorn_error_logger.handlers:
        for existing in gunicorn_error_logger.handlers:
            existing.addFilter(RequestIDFilter())
            existing.setFormatter(formatter)
            existing.setLevel(log_level)
            app.logger.addHandler(existing)
    else:
        app.logger.addHandler(handler)

    app.logger.setLevel(log_level)


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    configure_logging(app)

    # Asegura DATA_DIR y muestra la URI (útil en logs de Render)
    data_dir = Path(app.config["DATA_DIR"])
    data_dir.mkdir(parents=True, exist_ok=True)
    app.logger.info("DB URI -> %s", app.config["SQLALCHEMY_DATABASE_URI"])

    # Directorios persistentes (DATA_DIR, instance/, etc.)
    ensure_dirs(app)

    # DB
    db.init_app(app)
    init_migrations(app, db)
    init_auth_extensions(app)

    set_security_headers(app)

    @app.before_request
    def _assign_request_id():  # pragma: no cover - trivial
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_id = request_id

    @app.after_request
    def _add_request_id_header(response):  # pragma: no cover - simple header
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers.setdefault("X-Request-ID", request_id)
        return response

    # Variables globales seguras para Jinja (evita usar `current_app` en plantillas)
    @app.context_processor
    def inject_globals():
        try:
            view_functions = app.view_functions
            has_web_index = "web.index" in view_functions
            has_web_upload = "web.upload" in view_functions
        except Exception:
            has_web_index = False
            has_web_upload = False
        return {
            "has_web_index": has_web_index,
            "has_web_upload": has_web_upload,
            "config": app.config,
        }

    # Blueprints
    from . import models  # noqa: F401
    from .api import v1 as _api_v1  # noqa: F401

    app.register_blueprint(public_bp)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")
    app.register_blueprint(bp_ping)

    # Exentamos la API pública JSON del CSRF global
    csrf.exempt(bp_api_v1)
    limiter.exempt(bp_ping)

    register_cli(app)

    @app.errorhandler(Exception)
    def handle_any_error(err):  # pragma: no cover - logging side-effect
        if isinstance(err, HTTPException):
            return err
        app.logger.exception("Unhandled exception")
        return ("", 500)

    secret_key = app.config.get("SECRET_KEY", "")
    if not secret_key or len(secret_key) < 32:
        app.logger.warning(
            "SECRET_KEY is shorter than 32 characters. Provide a secure 32+ byte key for production.",
        )

    return app
