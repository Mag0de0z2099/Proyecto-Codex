"""Blueprint con endpoints básicos de salud para la API v1."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify

bp_api_v1 = Blueprint("api_v1", __name__)


@bp_api_v1.get("/health")
def health() -> tuple[Response, int]:
    """Endpoint de healthcheck usado por Render."""
    return jsonify(status="ok"), 200
