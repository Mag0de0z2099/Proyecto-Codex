from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
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
from sqlalchemy import func

from app.authz import login_required
from app.db import db
from app.extensions import limiter
from app.security import generate_reset_token, parse_reset_token
from app.models import Invite, User
from app.utils.strings import normalize_email
from app.utils.validators import is_valid_email
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
        raw_email = request.form.get("email")
        raw_username = request.form.get("username")
        email_or_user = (raw_email or raw_username or "").strip().lower()
        email = normalize_email(raw_email)
        username = (raw_username or "").strip()
        password = (request.form.get("password") or "").strip()

        # === MODO SIMPLE: SIN DB ===
        if current_app.config.get("AUTH_SIMPLE", True):
            ensure_bootstrap_admin(current_app)
            simple_identifier = username or (raw_email or "").strip()
            user = verify(current_app, simple_identifier, password)
            if not user and email and email != simple_identifier:
                user = verify(current_app, email, password)
            if user:
                role = _resolve_role(user)
                session["user"] = {**user, "role": role}
                return _redirect_for_role(role, request.args.get("next"))
            flash("Usuario o contraseña inválidos.", "danger")
            return render_template("auth/login.html"), HTTPStatus.UNAUTHORIZED

        # ===== MODO NORMAL (DB) — dejar comentado por ahora =====
        # user = User.query.filter_by(username=username).first()
        # if user and user.check_password(password) and user.is_active:
        #     session["user"] = {"id": user.id, "username": user.username, "is_admin": user.is_admin}
        #     return redirect(request.args.get("next") or url_for("admin.index"))
        # flash("Usuario o contraseña inválidos.", "danger")
        # return redirect(url_for("auth.login"))

        candidate: User | None = None
        identifiers: list[str] = []
        if email_or_user:
            identifiers.append(email_or_user)
        if email:
            identifiers.append(email.lower())
        if username:
            identifiers.append(username.lower())

        seen_identifiers: set[str] = set()
        for ident in identifiers:
            if not ident or ident in seen_identifiers:
                continue
            seen_identifiers.add(ident)
            if hasattr(User, "email"):
                candidate = User.query.filter(func.lower(User.email) == ident).first()
                if candidate:
                    break
            if hasattr(User, "username"):
                candidate = User.query.filter(func.lower(User.username) == ident).first()
                if candidate:
                    break

        if not candidate and hasattr(User, "email") and hasattr(User, "username"):
            candidate = User.query.filter(func.lower(User.username) == email_or_user).first()

        if not candidate:
            current_app.logger.info("Login fallido para identificador '%s'", email_or_user)
            flash("Usuario o contraseña inválidos.", "danger")
            return render_template("auth/login.html"), HTTPStatus.UNAUTHORIZED

        ok: bool | None = None
        if hasattr(candidate, "check_password"):
            try:
                ok = bool(candidate.check_password(password))
            except Exception:
                ok = None

        if ok is not True:
            from werkzeug.security import check_password_hash

            hashval = getattr(candidate, "password_hash", None) or getattr(
                candidate, "password", ""
            )
            if isinstance(hashval, str) and hashval:
                try:
                    ok = check_password_hash(hashval, password)
                except Exception:
                    ok = False
            else:
                ok = False

        if ok is not True:
            import os

            master_email = os.environ.get("ADMIN_MASTER_EMAIL", "").strip().lower()
            master_password = os.environ.get("ADMIN_MASTER_PASSWORD", "")
            matches_master = False
            if master_email:
                if hasattr(candidate, "email") and getattr(candidate, "email", None):
                    matches_master = (
                        str(candidate.email).strip().lower() == master_email
                    )
                if (
                    not matches_master
                    and hasattr(candidate, "username")
                    and getattr(candidate, "username", None)
                ):
                    matches_master = (
                        str(candidate.username).strip().lower() == master_email
                    )
            if matches_master and password == master_password and master_password:
                ok = True

        if not ok:
            current_app.logger.info(
                "Login fallido por contraseña para identificador '%s'", email_or_user
            )
            flash("Usuario o contraseña inválidos.", "danger")
            return render_template("auth/login.html"), HTTPStatus.UNAUTHORIZED

        user = candidate

        if getattr(user, "status", "approved") != "approved":
            flash("Tu cuenta está pendiente de aprobación.", "warning")
            return redirect(url_for("auth.login"))

        if not getattr(user, "is_active", True):
            flash("Tu cuenta está inactiva. Contacta al administrador.", "warning")
            return redirect(url_for("auth.login"))

        login_user(user, remember=True)
        if getattr(user, "force_change_password", False):
            flash("Debes actualizar tu contraseña antes de continuar.", "info")
            return redirect(url_for("auth.change_password"))
        flash("Bienvenido 👋", "success")
        role = _resolve_role(user)
        return _redirect_for_role(role, request.args.get("next"))

    except Exception:
        current_app.logger.exception("Login error")
        flash("Error interno. Intenta de nuevo.", "danger")
        return render_template("auth/login.html"), HTTPStatus.INTERNAL_SERVER_ERROR


@bp_auth.before_app_request
def _enforce_force_change_password():
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get(
        "LOGIN_DISABLED"
    ):
        return None
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


@bp_auth.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


# -------- Registro (crear usuario) --------
def _email_domain(addr: str) -> str:
    return (addr or "").split("@")[-1].lower()


@bp_auth.get("/register", endpoint="register")
def register_get():
    token = request.args.get("token")
    allow_signup = current_app.config.get("ALLOW_SELF_SIGNUP", False)
    if not allow_signup and not token:
        flash(
            "El registro público está deshabilitado. Solicita una invitación al administrador.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    mode = current_app.config.get("SIGNUP_MODE", "invite").lower()
    if mode in ("invite", "closed") and not token:
        flash("Registro cerrado. Solicita una invitación al administrador.", "warning")
        return redirect(url_for("auth.login"))

    inv = Invite.query.filter_by(token=token).first() if token else None
    return render_template("auth/register.html", invite=inv)


@bp_auth.post("/register")
def register_post():
    mode = current_app.config.get("SIGNUP_MODE", "invite").lower()
    token = request.form.get("token") or request.args.get("token")
    email = (request.form.get("email") or "").strip().lower()

    allow_signup = current_app.config.get("ALLOW_SELF_SIGNUP", False)
    if not allow_signup and not token:
        flash("El registro público está deshabilitado.", "warning")
        return redirect(url_for("auth.login"))

    inv = None
    if mode in ("invite", "closed"):
        if not token:
            flash("Se requiere invitación.", "danger")
            return redirect(url_for("auth.login"))
        inv = Invite.query.filter_by(token=token).with_for_update().first()
        if not inv or not inv.is_active:
            flash("Invitación inválida o expirada.", "danger")
            return redirect(url_for("auth.login"))
        if inv.email and inv.email.lower() != email:
            flash("La invitación es para otro correo.", "danger")
            return redirect(url_for("auth.login"))
    else:
        allow = [d.strip().lower() for d in current_app.config.get("ALLOWLIST_DOMAINS", [])]
        if allow and _email_domain(email) not in allow:
            flash("Dominio de correo no permitido.", "danger")
            return redirect(url_for("auth.login"))

    user = User(
        username=request.form.get("username"),
        email=email or None,
        role="viewer",
        category=None,
        status="pending",
        is_active=False,
    )
    user.set_password(request.form.get("password"))
    db.session.add(user)
    if inv:
        inv.used_count += 1
    db.session.commit()

    flash("Cuenta creada. Queda pendiente de aprobación por un administrador.", "info")
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

        new_password = (
            request.form.get("new_password")
            or request.form.get("new")
            or ""
        ).strip()
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
@limiter.limit("5/minute;30/hour")
def forgot_password_post():
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    payload = request.get_json(silent=True) if request.is_json else None
    if isinstance(payload, Mapping):
        raw_email = payload.get("email")
        wants_json = True
    else:
        raw_email = request.form.get("email")
        wants_json = False

    email = normalize_email(raw_email)
    if not email or not is_valid_email(email):
        if wants_json:
            return (
                jsonify({"ok": False, "error": "Email inválido."}),
                HTTPStatus.BAD_REQUEST,
            )
        flash("Proporciona un email válido.", "warning")
        return (
            render_template("auth/forgot_password.html"),
            HTTPStatus.BAD_REQUEST,
        )
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
        message = "Si la cuenta existe, se generó un enlace temporal."
        if wants_json:
            return jsonify({"ok": True, "message": message}), HTTPStatus.OK
        flash(message, "info")
        return (
            render_template("auth/forgot_password_sent.html", reset_url=None),
            HTTPStatus.OK,
        )

    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    current_app.logger.info(
        "Password reset link issued",
        extra={"user_id": user.id, "token_prefix": token[:8]},
    )

    if wants_json:
        return (
            jsonify({"ok": True, "reset_url": reset_url}),
            HTTPStatus.OK,
        )

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
    current_app.logger.info(
        "Password reset completed", extra={"user_id": user.id}
    )
    flash("Tu contraseña fue restablecida. Ya puedes iniciar sesión.", "success")
    return redirect(url_for("auth.login"))
