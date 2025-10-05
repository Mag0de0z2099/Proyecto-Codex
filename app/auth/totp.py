from __future__ import annotations

import pyotp
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
from flask_login import current_user, login_required, login_user

from app import db
from app.models.user import User


def _issuer_name() -> str:
    return current_app.config.get("APP_NAME", "SGC")


totp_bp = Blueprint(
    "totp",
    __name__,
    url_prefix="/auth/totp",
    template_folder="templates",
)


def _clear_totp_session() -> None:
    for key in ("2fa_uid", "2fa_next", "2fa_remember", "2fa_force_change"):
        session.pop(key, None)


@totp_bp.route("/setup", methods=["GET", "POST"])
@login_required
def totp_setup():
    secret = current_user.totp_secret
    if request.method == "POST":
        secret = pyotp.random_base32()
        current_user.totp_secret = secret
        db.session.commit()
        flash("MFA habilitado", "success")
        return redirect(url_for("totp.totp_setup"))

    uri = None
    if secret:
        identifier = current_user.email or current_user.username or str(current_user.id)
        uri = pyotp.TOTP(secret).provisioning_uri(name=identifier, issuer_name=_issuer_name())
    return render_template("auth/totp_setup.html", secret=secret, uri=uri)


@totp_bp.route("/verify", methods=["GET", "POST"])
def totp_verify():
    uid = session.get("2fa_uid")
    if not uid:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, uid)
    if not user or not getattr(user, "totp_secret", None):
        _clear_totp_session()
        return redirect(url_for("auth.login"))

    uri = pyotp.TOTP(user.totp_secret).provisioning_uri(
        name=user.email or user.username or str(user.id),
        issuer_name=_issuer_name(),
    )

    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            remember = session.pop("2fa_remember", True)
            next_url = session.pop("2fa_next", None)
            force_change = session.pop("2fa_force_change", False)
            session.pop("2fa_uid", None)
            login_user(user, remember=remember)
            flash("Bienvenido 👋", "success")
            if force_change and getattr(user, "force_change_password", False):
                flash("Debes actualizar tu contraseña antes de continuar.", "info")
                return redirect(url_for("auth.change_password"))
            if next_url:
                return redirect(next_url)
            from app.blueprints.auth.routes import _redirect_for_role, _resolve_role

            role = _resolve_role(user)
            return _redirect_for_role(role)
        flash("Código inválido", "danger")
    return render_template("auth/totp_verify.html", uri=uri)
