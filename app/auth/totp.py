"""Blueprint to manage Time-based One-Time Password (TOTP) flows."""

from __future__ import annotations

import pyotp
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_user

from app.db import db
from app.extensions import limiter
from app.models.user import User
from app.security.audit import log_event
from app.security.flags import is_2fa_enabled


totp_bp = Blueprint("totp", __name__, url_prefix="/auth/totp", template_folder="templates")


@totp_bp.route("/setup", methods=["GET", "POST"])
def totp_setup():
    """Allow a user in the MFA flow to enrol."""

    if not is_2fa_enabled():
        session.pop("2fa_uid", None)
        flash("MFA deshabilitado", "info")
        return redirect(url_for("auth.login"))

    uid = session.get("2fa_uid")
    if not uid:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, uid)
    if not user:
        session.pop("2fa_uid", None)
        return redirect(url_for("auth.login"))

    secret = getattr(user, "totp_secret", None)

    if request.method == "POST":
        if not secret:
            secret = pyotp.random_base32()
            user.totp_secret = secret
            db.session.commit()
            flash("MFA habilitado", "success")
            return redirect(url_for("totp.totp_verify"))
        flash("MFA ya estaba habilitado.", "info")

    uri = None
    if secret:
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=_user_identifier(user), issuer_name="SGC"
        )

    return render_template("auth/totp_setup.html", secret=secret, uri=uri)


# ⬇️ Rate limit MFA verify: 6 por minuto
@limiter.limit("6 per minute", methods=["POST"])
@totp_bp.route("/verify", methods=["GET", "POST"])
def totp_verify():
    """Verify the MFA code after password authentication."""

    uid = session.get("2fa_uid")
    if not uid:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, uid)
    if not user or not getattr(user, "totp_secret", None):
        session.pop("2fa_uid", None)
        session.pop("2fa_next", None)
        session.pop("2fa_remember", None)
        return redirect(url_for("auth.login"))

    if not is_2fa_enabled():
        remember_flag = session.pop("2fa_remember", None)
        remember = True if remember_flag is None else bool(remember_flag)
        next_url = session.pop("2fa_next", None)
        session.pop("2fa_uid", None)
        log_event("login_success", user_id=user.id)
        login_user(user, remember=remember)
        from app.auth.routes import _redirect_for_role  # lazy import

        role = _resolve_role_for_user(user)
        if getattr(user, "force_change_password", False):
            flash("Debes actualizar tu contraseña antes de continuar.", "info")
            return redirect(url_for("auth.change_password"))
        flash("Autenticación verificada", "success")
        if next_url:
            return redirect(next_url)
        return _redirect_for_role(role)

    totp = pyotp.TOTP(user.totp_secret)

    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        if totp.verify(code, valid_window=1):
            remember_flag = session.pop("2fa_remember", None)
            remember = True if remember_flag is None else bool(remember_flag)
            next_url = session.pop("2fa_next", None)
            session.pop("2fa_uid", None)
            log_event("login_success", user_id=user.id)
            login_user(user, remember=remember)
            from app.auth.routes import _redirect_for_role  # lazy import

            role = _resolve_role_for_user(user)
            if getattr(user, "force_change_password", False):
                flash("Debes actualizar tu contraseña antes de continuar.", "info")
                return redirect(url_for("auth.change_password"))
            flash("Autenticación verificada", "success")
            if next_url:
                return redirect(next_url)
            return _redirect_for_role(role)
        log_event("login_fail", user_id=user.id)
        flash("Código inválido", "danger")

    uri = totp.provisioning_uri(
        name=_user_identifier(user),
        issuer_name="SGC",
    )
    return render_template("auth/totp_verify.html", uri=uri)


def _resolve_role_for_user(user: User) -> str:
    from app.auth.routes import _resolve_role

    return _resolve_role(user)


def _user_identifier(user: User) -> str:
    return user.email or getattr(user, "username", f"user-{user.id}") or f"user-{user.id}"


__all__ = ["totp_bp"]
