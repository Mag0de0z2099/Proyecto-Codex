from __future__ import annotations
from flask import Blueprint

from .v1.health import bp as health_bp

bp_api = Blueprint("api", __name__)


def register_blueprints(app):
    """Registrar blueprints de la API pública."""

    app.register_blueprint(health_bp)
    return {health_bp.name: health_bp}
