"""Healthcheck endpoint con verificación de base de datos."""

from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import text

from app.db import db

bp = Blueprint("health", __name__, url_prefix="/healthz")


@bp.get("")
def healthz():
    ok_db = True
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - el healthcheck no falla en tests
        ok_db = False
    return jsonify({"ok": True, "db": ok_db})
