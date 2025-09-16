"""Paquete de la aplicación Flask para Proyecto-Codex."""

from __future__ import annotations

import logging
from flask import Flask

from .config import get_config
from .extensions import init_extensions
from .errors import register_error_handlers
from .blueprints.web import bp_web
from .blueprints.api.v1 import bp_api_v1

__all__ = ["create_app", "__version__"]

__version__ = "0.1.0"


def create_app(config_name: str | None = None) -> Flask:
    """Crea y configura una instancia de :class:`~flask.Flask`."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    if not app.debug:
        gunicorn_error_logger = logging.getLogger("gunicorn.error")
        if gunicorn_error_logger.handlers:
            app.logger.handlers = gunicorn_error_logger.handlers
            app.logger.setLevel(gunicorn_error_logger.level)
        else:  # pragma: no cover - fallback para entornos sin Gunicorn
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            app.logger.addHandler(handler)
            app.logger.setLevel(logging.INFO)

    init_extensions(app)

    app.register_blueprint(bp_web)
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")

    register_error_handlers(app)
    return app
