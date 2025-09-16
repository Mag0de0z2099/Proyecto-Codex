"""Blueprint sencilla para el área administrativa."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session


SESSION_KEY = "admin_authenticated"


bp = Blueprint("admin", __name__, url_prefix="/admin")


def _is_authenticated() -> bool:
    return session.get(SESSION_KEY) is True


def _require_password() -> str:
    return current_app.config.get("ADMIN_PASSWORD", "admin")


@bp.get("/", strict_slashes=False)
def admin_index():
    if not _is_authenticated():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"area": "admin", "status": "ok"})


@bp.post("/login")
def admin_login():
    payload = request.get_json(silent=True) or {}
    password = payload.get("password")
    if password == _require_password():
        session[SESSION_KEY] = True
        return jsonify({"ok": True})
    session.pop(SESSION_KEY, None)
    return jsonify({"ok": False, "error": "bad credentials"}), 401


@bp.post("/logout")
def admin_logout():
    session.pop(SESSION_KEY, None)
    return jsonify({"ok": True})
