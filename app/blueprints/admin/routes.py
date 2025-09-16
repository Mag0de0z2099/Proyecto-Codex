"""Rutas para la zona administrativa."""

from __future__ import annotations

from flask import current_app, jsonify, render_template, request, session

from . import bp_admin


@bp_admin.get("/")
def admin_home():
    """Zona protegida que requiere sesión de administrador."""

    if session.get("admin"):
        return jsonify(area="admin", status="ok"), 200
    return jsonify(error="unauthorized"), 401


@bp_admin.post("/login")
def admin_login():
    """Autenticar al usuario administrador mediante una contraseña simple."""

    data = request.get_json(silent=True) or {}
    password = data.get("password")
    if password and password == current_app.config.get("ADMIN_PASSWORD", "admin"):
        session["admin"] = True
        return jsonify(ok=True), 200
    return jsonify(ok=False, error="bad credentials"), 401


@bp_admin.post("/logout")
def admin_logout():
    """Cerrar la sesión de administrador."""

    session.pop("admin", None)
    return jsonify(ok=True), 200


@bp_admin.get("/ui")
def admin_ui():
    """Servir una interfaz mínima para gestionar el login del administrador."""

    return render_template("admin_ui.html")
