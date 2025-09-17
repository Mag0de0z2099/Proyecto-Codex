from __future__ import annotations

import re
from http import HTTPStatus

from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

from app.db import db
from app.models.user import User
from app.security import generate_reset_token, parse_reset_token

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
    if getattr(user, "force_change_password", False):
        flash("Debes actualizar tu contraseña antes de continuar.", "info")
        return redirect(url_for("auth.change_password"))
    flash("Bienvenido 👋", "success")
    return redirect(url_for("admin.index"))


@bp_auth.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))


@bp_auth.get("/change-password")
@login_required
def change_password():
    return render_template("auth/change_password.html")


@bp_auth.post("/change-password")
@login_required
def change_password_post():
    current = request.form.get("current") or ""
    new = request.form.get("new") or ""
    confirm = request.form.get("confirm") or ""

    if not current_user.check_password(current):
        flash("Tu contraseña actual no es correcta.", "danger")
        return redirect(url_for("auth.change_password"))

    if len(new) < 8:
        flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("auth.change_password"))

    if new != confirm:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect(url_for("auth.change_password"))

    current_user.set_password(new)
    current_user.force_change_password = False
    db.session.commit()
    flash("Contraseña actualizada.", "success")
    return redirect(url_for("admin.index"))


@bp_auth.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    return render_template("auth/forgot_password.html")


@bp_auth.post("/forgot-password")
def forgot_password_post():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    email = (request.form.get("email") or "").strip().lower()
    user = db.session.query(User).filter_by(email=email).one_or_none()

    # Siempre mensaje neutro
    if not user:
        flash("Si la cuenta existe, se generó un enlace temporal.", "info")
        return (
            render_template("auth/forgot_password_sent.html", reset_url=None),
            HTTPStatus.OK,
        )

    # Generar token y MOSTRAR el link en pantalla (sin correo)
    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    # También lo dejamos en logs
    from flask import current_app

    current_app.logger.warning("[RESET-LINK] %s -> %s", user.email, reset_url)

    flash("Se generó un enlace temporal. Úsalo antes de 1 hora.", "success")
    return (
        render_template("auth/forgot_password_sent.html", reset_url=reset_url),
        HTTPStatus.OK,
    )


@bp_auth.get("/reset-password/<token>")
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    email = parse_reset_token(token)
    if not email:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@bp_auth.post("/reset-password/<token>")
def reset_password_post(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    email = parse_reset_token(token)
    if not email:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))

    new = request.form.get("new") or ""
    confirm = request.form.get("confirm") or ""

    if len(new) < 8:
        flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("auth.reset_password", token=token))

    if new != confirm:
        flash("Las contraseñas no coinciden.", "danger")
        return redirect(url_for("auth.reset_password", token=token))

    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))

    user.set_password(new)
    db.session.commit()
    flash("Tu contraseña fue restablecida. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))
