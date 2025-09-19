from __future__ import annotations

import re
from http import HTTPStatus
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required as flask_login_required, login_user, logout_user

from app.db import db
from app.security import generate_reset_token, parse_reset_token
from app.simple_auth.store import add_user, ensure_bootstrap_admin, verify

bp_auth = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")


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
                session["user"] = user
                return redirect(request.args.get("next") or url_for("admin.index"))
            flash("Usuario o contraseña inválidos.", "danger")
            return redirect(url_for("auth.login"))

        # ===== MODO NORMAL (DB) — dejar comentado por ahora =====
        # user = User.query.filter_by(username=username).first()
        # if user and user.check_password(password) and user.is_active:
        #     session["user"] = {"id": user.id, "username": user.username, "is_admin": user.is_admin}
        #     return redirect(request.args.get("next") or url_for("admin.index"))
        # flash("Usuario o contraseña inválidos.", "danger")
        # return redirect(url_for("auth.login"))

        from app.models.user import User

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            if getattr(user, "force_change_password", False):
                flash("Debes actualizar tu contraseña antes de continuar.", "info")
                return redirect(url_for("auth.change_password"))
            flash("Bienvenido 👋", "success")
            return redirect(request.args.get("next") or url_for("admin.index"))

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
        return redirect(url_for("admin.index"))
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
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
@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    if not current_app.config.get("AUTH_SIMPLE", True):
        abort(404)

    allow_open = current_app.config.get("AUTH_SIMPLE_SELF_REGISTER", "1") == "1"
    is_admin = bool(session.get("user", {}).get("is_admin"))

    if request.method == "POST":
        if not allow_open and not is_admin:
            flash("Solo el administrador puede crear usuarios.", "warning")
            return redirect(url_for("auth.login"))

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        make_admin = bool(request.form.get("is_admin")) if is_admin else False

        if len(username) < 3:
            flash("El usuario debe tener al menos 3 caracteres.", "warning")
            return render_template("auth/register.html", is_admin=is_admin)
        if len(password) < 4:
            flash("La contraseña debe tener al menos 4 caracteres.", "warning")
            return render_template("auth/register.html", is_admin=is_admin)
        if password != confirm:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("auth/register.html", is_admin=is_admin)

        try:
            add_user(current_app, username, password, make_admin)
            flash("Usuario creado. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("auth/register.html", is_admin=is_admin)

    return render_template("auth/register.html", is_admin=is_admin)


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
    from app.models.user import User
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

    from app.models.user import User
    user = db.session.query(User).filter_by(email=email).one_or_none()
    if not user:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))

    user.set_password(new)
    db.session.commit()
    flash("Tu contraseña fue restablecida. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))
