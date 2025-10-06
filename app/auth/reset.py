"""Blueprint implementing password reset via signed tokens."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.db import db
from app.models.user import User
from app.security.policy import password_ok


reset_bp = Blueprint(
    "reset", __name__, url_prefix="/auth/reset", template_folder="templates"
)


def _ts(app) -> URLSafeTimedSerializer:
    secret_key = app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key, salt="pwd-reset")


def _send_reset_email(to_email, reset_url):
    cfg = current_app.config
    if not cfg["MAIL_SERVER"] or not cfg["MAIL_USERNAME"] or not cfg["MAIL_PASSWORD"]:
        current_app.logger.warning("SMTP no configurado; URL de reset: %s", reset_url)
        return
    msg = EmailMessage()
    msg["Subject"] = "SGC - Recuperar contraseña"
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = to_email
    msg.set_content(
        f"Usa este enlace para restablecer tu contraseña (30 min): {reset_url}"
    )
    ctx = ssl.create_default_context()
    with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"]) as s:
        if cfg["MAIL_USE_TLS"]:
            s.starttls(context=ctx)
        s.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
        s.send_message(msg)


@reset_bp.route("/request", methods=["GET", "POST"])
def reset_request():
    """Request a password reset token."""

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = _ts(current_app).dumps({"uid": user.id})
            url = url_for("reset.reset_confirm", token=token, _external=True)
            _send_reset_email(user.email, url)
        flash("Si el correo existe, enviamos instrucciones.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_request.html")


@reset_bp.route("/confirm/<token>", methods=["GET", "POST"])
def reset_confirm(token: str):
    """Confirm the reset token and set a new password."""

    try:
        data = _ts(current_app).loads(token, max_age=1800)
    except SignatureExpired:
        flash("Token expirado", "warning")
        return redirect(url_for("reset.reset_request"))
    except BadSignature:
        flash("Token inválido", "danger")
        return redirect(url_for("reset.reset_request"))

    user = db.session.get(User, data.get("uid")) if data else None
    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("reset.reset_request"))

    if request.method == "POST":
        pwd = request.form.get("password") or ""
        if not password_ok(pwd):
            flash(
                "Contraseña débil: usa ≥12 caracteres, mayúsculas, minúsculas y dígitos.",
                "warning",
            )
            return render_template("auth/reset_confirm.html", policy_hint=_POLICY_HINT)
        user.set_password(pwd)
        db.session.commit()
        flash("Contraseña actualizada", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_confirm.html", policy_hint=_POLICY_HINT)


_POLICY_HINT = "Usa al menos 12 caracteres con mayúsculas, minúsculas y dígitos."


__all__ = ["reset_bp"]
