"""Paquete principal de la aplicación Flask para Proyecto-Codex."""

from __future__ import annotations

from flask import Flask

from .blueprints.api.v1 import bp_api_v1
from .blueprints.web import bp_web
from .config import get_config

__all__ = ["create_app", "__version__"]

__version__ = "0.1.0"


def create_app(config_name: str | None = None) -> Flask:
    """Crear y configurar una instancia de :class:`~flask.Flask`."""

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Registro de blueprints
    app.register_blueprint(bp_web)
    app.register_blueprint(bp_api_v1, url_prefix="/api/v1")

    return app
