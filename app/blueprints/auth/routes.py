from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.db import db
from app.models.user import User

from . import bp_auth


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
