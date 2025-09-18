"""Blueprint con endpoints básicos de salud para la API v1."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify
from sqlalchemy import text

from app.db import db

bp_api_v1 = Blueprint("api_v1", __name__)


@bp_api_v1.get("/health")
def health() -> tuple[Response, int]:
    """Endpoint de healthcheck usado por Render."""
    try:
        db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
        return jsonify(status="ok", db="users:ready"), 200
    except Exception:
        return jsonify(status="ok", db="users:missing"), 200
