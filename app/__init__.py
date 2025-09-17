"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
from flask import Flask

from .api.v1 import bp as bp_api_v1
from .blueprints.admin import bp_admin
from .blueprints.auth import bp_auth
from .config import get_config
from .db import db
from .extensions import init_auth_extensions
from .migrate_ext import init_migrations
from .blueprints.web import bp_web
from .storage import ensure_dirs


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Directorios persistentes (DATA_DIR, instance/, etc.)
    ensure_dirs(app)

    # Log de Gunicorn en producción (Render)
    if not app.debug:
        gunicorn_error_logger = logging.getLogger("gunicorn.error")
        if gunicorn_error_logger.handlers:
            app.logger.handlers = gunicorn_error_logger.handlers
            app.logger.setLevel(gunicorn_error_logger.level)

    # DB
    db.init_app(app)
    init_migrations(app, db)
    init_auth_extensions(app)

    # Variables globales seguras para Jinja (evita usar `current_app` en plantillas)
    @app.context_processor
    def inject_nav_targets():
        try:
            has_web_index = "web.index" in app.view_functions
        except Exception:
            has_web_index = False
        return {"has_web_index": has_web_index}

    # Blueprints
    from . import models  # noqa: F401

    app.register_blueprint(bp_auth, url_prefix="/auth")
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_admin, url_prefix="/admin")
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")

    return app
