from __future__ import annotations

import logging
import re
from http import HTTPStatus

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    current_user,
    login_required as flask_login_required,
    login_user,
    logout_user,
)

from app.db import db
from app.models.user import User
from app.security import generate_reset_token, parse_reset_token

from app.authz import login_required as simple_login_required

from . import bp_auth


# Credenciales en memoria para el modo simple
SIMPLE_USERS = {
    "admin": "admin",
    "test": "test",
}

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp_auth.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    return render_template("auth/login.html")


@bp_auth.post("/login")
def login_post():
    try:
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if current_app.config.get("AUTH_SIMPLE", False):
            ok = SIMPLE_USERS.get(username) == password
            if ok:
                session.clear()
                session["user"] = {
                    "username": username,
                    "is_admin": username == "admin",
                }
                next_url = request.args.get("next") or url_for("admin.index")
                flash("Bienvenido 👋", "success")
                return redirect(next_url)

            flash("Usuario o contraseña inválidos.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password) or not user.is_active:
            flash("Credenciales inválidas o usuario inactivo.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        session["user"] = {
            "id": user.id,
            "username": user.username,
            "is_admin": getattr(user, "is_admin", False),
        }
        if getattr(user, "force_change_password", False):
            flash("Debes actualizar tu contraseña antes de continuar.", "info")
            return redirect(url_for("auth.change_password"))

        flash("Bienvenido 👋", "success")
        next_url = request.args.get("next") or url_for("admin.index")
        return redirect(next_url)
    except Exception:
        logger.exception("Login error")
        current_app.logger.exception("Login error")
        flash("Error interno. Intenta de nuevo en unos minutos.", "danger")
        return redirect(url_for("auth.login"))


@bp_auth.get("/logout")
@simple_login_required
def logout():
    if current_app.config.get("AUTH_SIMPLE", False):
        session.clear()
    else:
        session.pop("user", None)
        logout_user()

    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))


@bp_auth.route("/change-password", methods=["GET", "POST"])
@flask_login_required
def change_password():
    force_change = getattr(current_user, "force_change_password", False)
    template = (
        "auth/force_change_password.html"
        if force_change
        else "auth/change_password.html"
    )

    if request.method == "POST":
        if not force_change:
            current = (request.form.get("current") or "").strip()
            if not current_user.check_password(current):
                flash("Tu contraseña actual no es correcta.", "warning")
                return render_template(template)

        new_password = (request.form.get("new_password") or "").strip()
        confirm = (request.form.get("confirm") or "").strip()

        if len(new_password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "warning")
            return render_template(template)

        if new_password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template(template)

        current_user.set_password(new_password)
        if hasattr(current_user, "force_change_password"):
            current_user.force_change_password = False

        db.session.commit()
        message = "Tu contraseña ha sido actualizada. ¡Bienvenido!" if force_change else "Contraseña actualizada."
        flash(message, "success")
        return redirect(url_for("admin.index"))

    return render_template(template)


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
