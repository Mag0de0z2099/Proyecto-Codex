"""Fábrica de la app Flask para Codex."""

from __future__ import annotations

import logging
from flask import Flask

from .admin import bp as bp_admin
from .api.v1 import bp as bp_api_v1
from .config import get_config
from .db import db
from .migrate_ext import init_migrations
from .routes import bp as bp_web
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

    # Blueprints
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")

    return app
