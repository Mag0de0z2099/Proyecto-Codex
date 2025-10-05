from __future__ import annotations

import os
from collections.abc import Mapping
from http import HTTPStatus
from flask import (
    Blueprint,
    abort,
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
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

from app.authz import login_required
from app.db import db
from app.extensions import limiter
from app.security import generate_reset_token, parse_reset_token
from app.security.policy import is_locked, register_fail, reset_fail_counter
from app.models import Invite, User
from app.blueprints.auth.utils import (
    check_pwd_tolerant,
    is_active_and_approved,
    normalize_email,
)
from app.utils.validators import is_valid_email
from app.simple_auth.store import ensure_bootstrap_admin, verify

bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")
# ``bp_auth`` se mantiene como alias para compatibilidad retro.
bp_auth = bp


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


@bp.post("/login")
def login_post():
    email_input = request.form.get("email")
    username_input = request.form.get("username")

    identifier_source = email_input if email_input not in (None, "") else username_input
    identifier = (identifier_source or "").strip()
    password = (request.form.get("password") or request.form.get("pass") or "").strip()

    if not identifier or not password:
        flash("Faltan credenciales", "error")
        return redirect(url_for("auth.login"))

    email_from_field = (email_input or "").strip().casefold() or None
    email = email_from_field or (normalize_email(identifier) or None)
    if email:
        email = email.casefold()

    username = (username_input or "").strip()
    email_or_user = identifier.casefold()

    if current_app.config.get("AUTH_SIMPLE", True):
        ensure_bootstrap_admin(current_app)
        username_lookup = username or identifier
        user = verify(current_app, username_lookup or email_or_user, password)
        if not user and email and email != (username_lookup or "").casefold():
            user = verify(current_app, email, password)
        if user:
            role = _resolve_role(user)
            session["user"] = {**user, "role": role}
            return _redirect_for_role(role, request.args.get("next"))
        flash("Usuario o contraseña inválidos.", "danger")
        return redirect(url_for("auth.login"))

    candidate: User | None = None
    query = db.session.query(User)

    search_terms: list[str] = []
    seen_terms: set[str] = set()

    def _add_term(term: str | None) -> None:
        if not term:
            return
        normalized = term.casefold()
        if normalized not in seen_terms:
            seen_terms.add(normalized)
            search_terms.append(normalized)

    _add_term(email_or_user)
    _add_term(email)
    _add_term(username)

    for term in search_terms:
        if hasattr(User, "email"):
            candidate = query.filter(func.lower(User.email) == term).first()
            if candidate:
                break
        if hasattr(User, "username"):
            candidate = query.filter(func.lower(User.username) == term).first()
            if candidate:
                break

    if not candidate:
        current_app.logger.info("Login fallido para identificador '%s'", email_or_user)
        flash("Usuario/contraseña incorrectos", "error")
        return redirect(url_for("auth.login"))

    if is_locked(candidate):
        flash(
            "Cuenta bloqueada temporalmente. Intenta más tarde.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    ok: bool | None = None
    if hasattr(candidate, "check_password"):
        try:
            ok = bool(candidate.check_password(password))
        except Exception:
            ok = None

    if ok is not True:
        hashval = getattr(candidate, "password_hash", None) or getattr(
            candidate,
            "password",
            "",
        )
        ok = check_pwd_tolerant(hashval, password)

    if ok is not True:
        current_app.logger.info(
            "Login fallido por contraseña para identificador '%s'", email_or_user
        )
        try:
            register_fail(candidate)
        except Exception:
            current_app.logger.exception("No se pudo registrar el intento fallido")
        flash("Usuario/contraseña incorrectos", "error")
        return redirect(url_for("auth.login"))

    user = candidate

    if not is_active_and_approved(user):
        flash(
            "Tu cuenta está pendiente de aprobación o inactiva. Contacta al administrador.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    try:
        reset_fail_counter(user)
    except Exception:
        current_app.logger.exception("No se pudo reiniciar el contador de fallos")

    if getattr(user, "totp_secret", None):
        session["2fa_uid"] = user.id
        session["2fa_next"] = request.args.get("next")
        session["2fa_remember"] = True
        session["2fa_force_change"] = bool(getattr(user, "force_change_password", False))
        flash("Ingresa tu código de verificación.", "info")
        return redirect(url_for("totp.totp_verify"))

    login_user(user, remember=True)
    if getattr(user, "force_change_password", False):
        flash("Debes actualizar tu contraseña antes de continuar.", "info")
        return redirect(url_for("auth.change_password"))

    flash("Bienvenido 👋", "success")
    role = _resolve_role(user)
    return _redirect_for_role(role, request.args.get("next"))


@bp.before_app_request
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


@bp.get("/login")
def login():
    if current_app.config.get("AUTH_SIMPLE", True) and session.get("user"):
        role = _resolve_role(session.get("user"))
        return redirect(url_for(_endpoint_for_role(role)))
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


@bp.get("/dev-reset-admin")
def dev_reset_admin():
    if not current_app.config.get("LOGIN_DISABLED"):
        abort(404)

    token = request.args.get("token", "")
    expected = os.getenv("DEV_RESET_TOKEN", "")
    if not expected or token != expected:
        abort(403)

    email = normalize_email(os.getenv("DEV_ADMIN_EMAIL", "admin@admin.com"))
    password = os.getenv("DEV_ADMIN_PASS", "admin123")

    if not email:
        abort(400)

    query = db.session.query(User)

    def _fetch_user() -> User | None:
        if hasattr(User, "email"):
            return query.filter(func.lower(User.email) == email).first()
        if hasattr(User, "username"):
            return query.filter(func.lower(User.username) == email).first()
        return None

    try:
        user: User | None = _fetch_user()
    except OperationalError:
        db.session.rollback()
        db.create_all()
        query = db.session.query(User)
        user = _fetch_user()

    if not user:
        user = User()
        if hasattr(user, "email"):
            setattr(user, "email", email)
        elif hasattr(user, "username"):
            setattr(user, "username", email)
        db.session.add(user)

    if hasattr(user, "username") and not getattr(user, "username", None):
        try:
            username_candidate = email.split("@", 1)[0] or email
        except Exception:
            username_candidate = email
        setattr(user, "username", username_candidate)

    for attr in ("is_active", "active", "enabled", "aprobado", "is_approved", "approved", "is_admin"):
        if hasattr(user, attr):
            setattr(user, attr, True)

    for attr in ("status", "estado", "state"):
        if hasattr(user, attr):
            try:
                setattr(user, attr, "approved")
            except Exception:
                pass

    for attr in ("role", "rol", "perfil"):
        if hasattr(user, attr) and not getattr(user, attr):
            try:
                setattr(user, attr, "admin")
            except Exception:
                pass

    if hasattr(user, "password_hash"):
        setattr(user, "password_hash", generate_password_hash(password))
    elif hasattr(user, "set_password"):
        user.set_password(password)
    elif hasattr(user, "password"):
        setattr(user, "password", generate_password_hash(password))

    db.session.commit()

    return (
        f"OK: admin reset — email={email} pass={password}"
    )


# -------- Registro (crear usuario) --------
def _email_domain(addr: str) -> str:
    return (addr or "").split("@")[-1].lower()


@bp.get("/register", endpoint="register")
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


@bp.post("/register")
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

@bp.route("/change-password", methods=["GET", "POST"])
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


@bp.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    return render_template("auth/forgot_password.html")


@bp.post("/forgot-password")
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


@bp.get("/reset-password/<token>")
def reset_password(token: str):
    if current_user.is_authenticated:
        role = _resolve_role(current_user)
        return redirect(url_for(_endpoint_for_role(role)))
    email = parse_reset_token(token)
    if not email:
        flash("El enlace no es válido o expiró.", "danger")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@bp.post("/reset-password/<token>")
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
