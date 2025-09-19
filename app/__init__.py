"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask
from werkzeug.exceptions import HTTPException

from .blueprints.admin import bp_admin
from .blueprints.api.v1 import bp_api_v1
from .blueprints.auth import bp_auth
from .blueprints.folders import bp_folders
from .blueprints.ping import bp_ping
from .blueprints.web import bp_web
from .config import get_config
from .db import db
from .extensions import init_auth_extensions
from .migrate_ext import init_migrations
from .storage import ensure_dirs


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Log de Gunicorn en producción (Render)
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_error_logger.handlers or app.logger.handlers
    app.logger.setLevel(logging.INFO)

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

    # Variables globales seguras para Jinja (evita usar `current_app` en plantillas)
    @app.context_processor
    def inject_globals():
        try:
            has_web_index = "web.index" in app.view_functions
        except Exception:
            has_web_index = False
        return {"has_web_index": has_web_index}

    # Blueprints
    from . import models  # noqa: F401
    from .api import v1 as _api_v1  # noqa: F401

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_admin, url_prefix="/admin")
    app.register_blueprint(bp_folders, url_prefix="/folders")
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")
    app.register_blueprint(bp_ping)

    @app.errorhandler(Exception)
    def handle_any_error(err):  # pragma: no cover - logging side-effect
        if isinstance(err, HTTPException):
            return err
        app.logger.exception("Unhandled exception")
        return ("", 500)

    return app
