"""Paquete principal de la aplicación Flask para Proyecto-Codex."""

from __future__ import annotations

import logging

from flask import Flask

from .blueprints.admin import bp_admin
from .blueprints.api.v1 import bp_api_v1
from .blueprints.web import bp_web
from .config import get_config
from .db import db, init_db
from .migrate_ext import init_migrations
from .errors import register_error_handlers
from .extensions import init_extensions
from .storage import ensure_dirs

__all__ = ["create_app", "__version__"]

__version__ = "0.1.0"


def create_app(config_name: str | None = None) -> Flask:
    """Crear y configurar una instancia de :class:`~flask.Flask`."""

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    if not app.debug:
        gunicorn_error_logger = logging.getLogger("gunicorn.error")
        if gunicorn_error_logger.handlers:
            app.logger.handlers = gunicorn_error_logger.handlers
            app.logger.setLevel(gunicorn_error_logger.level)

    init_extensions(app)

    # Asegurar directorios persistentes (DATA_DIR)
    ensure_dirs(app)

    # Base de datos
    init_db(app)

    # Migraciones (Flask-Migrate / Alembic)
    init_migrations(app, db)

    # Ya no usamos create_all(); las tablas las crean las migraciones.
    # Si quisieras permitirlo en dev, podrías condicionar con un flag/env.
    from . import models  # noqa: F401  (asegura el registro de modelos)

    app.register_blueprint(bp_web)
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")
    app.register_blueprint(bp_admin, url_prefix="/admin")

    register_error_handlers(app)
    return app
