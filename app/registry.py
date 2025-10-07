"""Centraliza el registro de blueprints de la aplicación."""

from __future__ import annotations

from flask import Blueprint, Flask

from app.api.metrics import bp as metrics_bp
from app.api.version import bp as version_bp
from app.api.v1.todos import bp as todos_v1_bp
from app.api.v1.users import bp as users_v1_bp
from app.blueprints.admin import bp_admin
from app.blueprints.api.v1 import bp_api_v1
from app.blueprints.auth import bp_auth
from app.blueprints.equipos import bp as equipos_bp
from app.blueprints.operadores import bp as operadores_bp
from app.blueprints.ping import bp_ping
from app.blueprints.web import bp_web
from app.routes.assets import assets_bp
from app.routes.auth import bp as auth_api_bp
from app.api.v1.health import bp as health_bp
from app.routes.public import public_bp


def register_blueprints(app: Flask) -> dict[str, Blueprint]:
    """Registra todos los blueprints conocidos y devuelve un índice por nombre."""

    entries: list[tuple[Blueprint, dict[str, object]]] = [
        (public_bp, {}),
        (bp_auth, {}),
        (bp_web, {}),
        (equipos_bp, {}),
        (operadores_bp, {}),
        (bp_admin, {}),
        (bp_api_v1, {"url_prefix": "/api/v1"}),
        (todos_v1_bp, {}),
        (users_v1_bp, {}),
        (metrics_bp, {}),
        (version_bp, {}),
        (assets_bp, {}),
        (bp_ping, {}),
        (health_bp, {}),
        (auth_api_bp, {}),
    ]

    registry: dict[str, Blueprint] = {}
    for blueprint, options in entries:
        app.register_blueprint(blueprint, **options)
        registry[blueprint.name] = blueprint

    return registry
