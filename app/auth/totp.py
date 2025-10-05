"""Blueprint to manage Time-based One-Time Password (TOTP) flows."""

from __future__ import annotations

import pyotp
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user

from app.db import db
from app.models.user import User


totp_bp = Blueprint("totp", __name__, url_prefix="/auth/totp", template_folder="templates")


@totp_bp.route("/setup", methods=["GET", "POST"])
@login_required
def totp_setup():
    """Allow the authenticated user to enrol in MFA."""

    if request.method == "POST":
        secret = pyotp.random_base32()
        current_user.totp_secret = secret
        db.session.commit()
        flash(
            "MFA habilitado. Configura tu app de autenticación con la clave mostrada.",
            "success",
        )
        return redirect(url_for("totp.totp_setup"))

    secret = getattr(current_user, "totp_secret", None)
    uri = None
    if secret:
        uri = pyotp.TOTP(secret).provisioning_uri(
            name=_user_identifier(current_user), issuer_name="SGC"
        )

    return render_template("auth/totp_setup.html", secret=secret, uri=uri)


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

    provisioning_uri = pyotp.TOTP(user.totp_secret).provisioning_uri(
        name=_user_identifier(user),
        issuer_name="SGC",
    )

    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            remember_flag = session.pop("2fa_remember", None)
            remember = True if remember_flag is None else bool(remember_flag)
            next_url = session.pop("2fa_next", None)
            session.pop("2fa_uid", None)
            login_user(user, remember=remember)
            from app.auth.routes import _redirect_for_role  # lazy import

            role = _resolve_role_for_user(user)
            if getattr(user, "force_change_password", False):
                flash("Debes actualizar tu contraseña antes de continuar.", "info")
                return redirect(url_for("auth.change_password"))
            flash("Autenticación verificada", "success")
            return _redirect_for_role(role, next_url)
        flash("Código inválido", "danger")

    return render_template("auth/totp_verify.html", uri=provisioning_uri)


def _resolve_role_for_user(user: User) -> str:
    from app.auth.routes import _resolve_role

    return _resolve_role(user)


def _user_identifier(user: User) -> str:
    return user.email or getattr(user, "username", f"user-{user.id}") or f"user-{user.id}"


__all__ = ["totp_bp"]
