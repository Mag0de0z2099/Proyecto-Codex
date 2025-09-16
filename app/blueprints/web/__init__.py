"""Blueprint con rutas públicas del sitio."""

from __future__ import annotations

from flask import Blueprint

bp_web = Blueprint("web", __name__)


@bp_web.route("/")
def home() -> str:
    """Página principal simple."""
    return "Hola desde Elyra + Render 🚀"


@bp_web.route("/health")
def health() -> tuple[str, int]:
    """Endpoint de salud para Render."""
    return "ok", 200
