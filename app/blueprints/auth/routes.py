from __future__ import annotations

import re

from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

from app.db import db
from app.models.user import User

from . import bp_auth

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp_auth.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    return render_template("auth/login.html")


@bp_auth.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user or not user.check_password(password):
        flash("Credenciales inválidas", "danger")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Bienvenido 👋", "success")
    return redirect(url_for("admin.index"))


@bp_auth.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))


@bp_auth.get("/register")
def register():
    """Formulario de registro."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    return render_template("auth/register.html")


@bp_auth.post("/register")
def register_post():
    """Procesa el registro."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    # Validaciones simples
    if not EMAIL_RE.match(email):
        flash("Email inválido.", "danger")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("auth.register"))

    if password != confirm:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect(url_for("auth.register"))

    # Unicidad
    exists = db.session.query(User).filter_by(email=email).one_or_none()
    if exists:
        flash("Este email ya está registrado.", "danger")
        return redirect(url_for("auth.register"))

    # Crear usuario
    user = User(email=email, is_admin=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))
