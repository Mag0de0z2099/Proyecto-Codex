from __future__ import annotations

import re
from collections.abc import Mapping
from http import HTTPStatus
from flask import (
    Blueprint,
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
from sqlalchemy import func, inspect
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app.db import db
from app.security import generate_reset_token, parse_reset_token
from app.models import User
from app.utils.strings import normalize_email
from app.simple_auth.store import ensure_bootstrap_admin, verify

bp_auth = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")


def _resolve_role(entity: Mapping[str, object] | User | None) -> str:
    if isinstance(entity, Mapping):
        role = str(entity.get("role") or "").strip().lower()
        if role in {"admin", "supervisor", "editor", "viewer"}:
            return role
        if entity.get("is_admin"):
            return "admin"
        return "viewer"
    if isinstance(entity, User):
        role = getattr(entity, "role", None)
        if role:
            return role
        if getattr(entity, "is_admin", False):
            return "admin"
    return "viewer"


def _endpoint_for_role(role: str) -> str:
    view_functions = current_app.view_functions
    if role == "admin":
        return "admin.index"
    if role in {"supervisor", "editor"} and "web.upload" in view_functions:
        return "web.upload"
    if "web.index" in view_functions:
        return "web.index"
    return "admin.index"


def _redirect_for_role(role: str, next_url: str | None = None):
    if next_url:
        return redirect(next_url)
    return redirect(url_for(_endpoint_for_role(role)))


@bp_auth.post("/login")
def login_post():
    try:
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        # === MODO SIMPLE: SIN DB ===
        if current_app.config.get("AUTH_SIMPLE", True):
            ensure_bootstrap_admin(current_app)
            user = verify(current_app, username, password)
            if user:
                role = _resolve_role(user)
                session["user"] = {**user, "role": role}
                return _redirect_for_role(role, request.args.get("next"))
            flash("Usuario o contraseña inválidos.", "danger")
            return redirect(url_for("auth.login"))

        # ===== MODO NORMAL (DB) — dejar comentado por ahora =====
        # user = User.query.filter_by(username=username).first()
        # if user and user.check_password(password) and user.is_active:
        #     session["user"] = {"id": user.id, "username": user.username, "is_admin": user.is_admin}
        #     return redirect(request.args.get("next") or url_for("admin.index"))
        # flash("Usuario o contraseña inválidos.", "danger")
        # return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            if getattr(user, "force_change_password", False):
                flash("Debes actualizar tu contraseña antes de continuar.", "info")
                return redirect(url_for("auth.change_password"))
            flash("Bienvenido 👋", "success")
            role = _resolve_role(user)
            return _redirect_for_role(role, request.args.get("next"))

        flash("Usuario o contraseña inválidos.", "danger")
        return redirect(url_for("auth.login"))

    except Exception:
        current_app.logger.exception("Login error")
        flash("Error interno. Intenta de nuevo.", "danger")
        return redirect(url_for("auth.login"))


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp_auth.before_app_request
def _enforce_force_change_password():
    allowed = {"auth.logout", "auth.change_password", "static"}
    if (
        current_user.is_authenticated
        and getattr(current_user, "force_change_password", False)
    ):
        endpoint = request.endpoint or ""
        if endpoint not in allowed:
            return redirect(url_for("auth.change_password"))


@bp_auth.get("/login")
def login():
    if current_app.config.get("AUTH_SIMPLE", True) and session.get("user"):
        role = _resolve_role(session.get("user"))
        return redirect(url_for(_endpoint_for_role(role)))
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    return render_template("auth/login.html")


@bp_auth.get("/logout")
def logout():
    if current_app.config.get("AUTH_SIMPLE", True):
        session.clear()
        flash("Sesión cerrada.", "info")
        return redirect(url_for("web.index"))
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))


# -------- Registro (crear usuario) --------
@bp_auth.get("/register")
def register():
    try:
        insp = inspect(db.engine)
        if not insp.has_table("users"):
            db.create_all()
    except Exception:  # pragma: no cover - logging + flash side-effect
        current_app.logger.exception("Unable to ensure users table exists")
        flash(
            "No se pudo verificar/crear tablas. Reintenta o ejecuta migraciones.",
            "warning",
        )

    return render_template("auth/register.html")


@bp_auth.post("/register")
def register_post():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if not username or not password:
        flash("Usuario y contraseña son obligatorios.", "warning")
        return redirect(url_for("auth.register"))

    if password != confirm:
        flash("Las contraseñas no coinciden.", "warning")
        return redirect(url_for("auth.register"))

    try:
        insp = inspect(db.engine)
        if not insp.has_table("users"):
            db.create_all()

        new_user = User(
            username=username,
            email=None,
            role="viewer",
            password_hash=generate_password_hash(password),
            is_admin=False,
            is_active=True,
            force_change_password=False,
        )
        db.session.add(new_user)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        flash("Ese usuario ya existe. Elige otro.", "warning")
        return redirect(url_for("auth.register"))
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Unable to create user from register form")
        flash("No se pudo crear el usuario. Inténtalo de nuevo.", "danger")
        return redirect(url_for("auth.register"))

    flash("Usuario creado con éxito. Ya puedes iniciar sesión.", "success")
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
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))

    return render_template(template)


@bp_auth.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    return render_template("auth/forgot_password.html")


@bp_auth.post("/forgot-password")
def forgot_password_post():
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    raw_email = request.form.get("email")
    email = normalize_email(raw_email)
    from app.models import User
    user = None
    if email:
        user = (
            db.session.query(User)
            .filter(func.lower(User.email) == email)
            .one_or_none()
        )

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
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    email = parse_reset_token(token)
    if not email:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@bp_auth.post("/reset-password/<token>")
def reset_password_post(token: str):
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
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

    from app.models import User
    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))

    user.set_password(new)
    db.session.commit()
    flash("Tu contraseña fue restablecida. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))
