"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, Response, g, has_request_context, request
from pytz import timezone
from werkzeug.exceptions import HTTPException

from .blueprints.admin import bp_admin
from .blueprints.api.v1 import bp_api_v1
from .blueprints.auth import bp_auth
from .blueprints.ping import bp_ping
from .blueprints.web import bp_web
from .cli_sync import register_sync_cli
from .routes.assets import assets_bp
from .routes.public import public_bp
from .config import get_config
from .db import db
from .extensions import csrf, init_auth_extensions, limiter
from .metrics import cleanup_multiprocess_directory
from .utils.scan_lock import get_scan_lock
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

    db_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    app.logger.info("DB URI -> %s", db_uri)
    if db_uri.startswith("sqlite:///") and not db_uri.endswith(":memory:"):
        sqlite_path = Path(db_uri.replace("sqlite:///", "", 1)).expanduser().resolve()
        app.logger.info("[DEBUG] SQLite file -> %s", sqlite_path)

    # Directorios persistentes (DATA_DIR, instance/, etc.)
    ensure_dirs(app)
    if os.getenv("PROMETHEUS_MULTIPROC_CLEAN_ON_START", "0").lower() in (
        "1",
        "true",
        "yes",
    ):
        cleanup_multiprocess_directory()

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
    app.register_blueprint(assets_bp)
    app.register_blueprint(bp_ping)

    # Exentamos la API pública JSON del CSRF global
    csrf.exempt(bp_api_v1)
    limiter.exempt(bp_ping)

    register_cli(app)
    register_sync_cli(app)

    @app.get("/metrics")
    def metrics():
        try:
            from prometheus_client import (
                CONTENT_TYPE_LATEST,
                CollectorRegistry,
                generate_latest,
                multiprocess,
            )

            registry = None
            if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
                registry = CollectorRegistry()
                multiprocess.MultiProcessCollector(registry)

            output = generate_latest(registry)
            return Response(output, mimetype=CONTENT_TYPE_LATEST)
        except Exception as e:
            return Response(
                f"# metrics unavailable: {e}\n",
                mimetype="text/plain",
                status=503,
            )

    if os.getenv("SCHEDULER_ENABLED", "0") == "1":
        from app.services.scanner import scan_all_folders

        tz_name = os.getenv("APP_TZ", "America/Monterrey")
        try:
            tz = timezone(tz_name)
        except Exception:  # pragma: no cover - defensive fallback
            tz = timezone("UTC")
            app.logger.warning(
                "APP_TZ inválida '%s', usando UTC como valor por defecto.", tz_name
            )

        try:
            interval_min = int(os.getenv("SCAN_INTERVAL_MIN", "15"))
        except ValueError:  # pragma: no cover - defensive fallback
            interval_min = 15
            app.logger.warning(
                "SCAN_INTERVAL_MIN inválido, usando 15 minutos por defecto."
            )

        scheduler = BackgroundScheduler(timezone=tz)

        def job() -> None:
            with app.app_context():
                try:
                    with get_scan_lock():
                        stats = scan_all_folders()
                        app.logger.info("[scanner] %s", stats)
                except TimeoutError:
                    app.logger.info("[scanner] saltado: lock ocupado.")

        scheduler.add_job(
            job,
            "interval",
            minutes=interval_min,
            id="scan_all_folders",
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        app.extensions.setdefault("apscheduler", scheduler)
        app.logger.info("Scheduler ON cada %s min (TZ=%s)", interval_min, tz)

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
