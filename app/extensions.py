"""Aplicaciones complementarias para la app Flask."""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def init_extensions(app: Flask) -> None:
    """Inicializa extensiones de terceros."""
    origins = app.config.get("ALLOWED_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": origins}})
