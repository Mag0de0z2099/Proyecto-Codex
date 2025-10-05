"""Blueprint implementing password reset via signed tokens."""

from __future__ import annotations

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
from app.security.policy import PASSWORD_MIN


reset_bp = Blueprint(
    "reset", __name__, url_prefix="/auth/reset", template_folder="templates"
)


def _serializer() -> URLSafeTimedSerializer:
    secret_key = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret_key, salt="pwd-reset")


@reset_bp.route("/request", methods=["GET", "POST"])
def reset_request():
    """Request a password reset token."""

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = _serializer().dumps({"uid": user.id})
            current_app.logger.info(
                "RESET URL: %s",
                url_for("reset.reset_confirm", token=token, _external=True),
            )
        flash("Si el correo existe, se enviaron instrucciones de recuperación.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_request.html")


@reset_bp.route("/confirm/<token>", methods=["GET", "POST"])
def reset_confirm(token: str):
    """Confirm the reset token and set a new password."""

    try:
        data = _serializer().loads(token, max_age=1800)
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
        password = request.form.get("password") or ""
        if len(password) < PASSWORD_MIN:
            flash(
                f"La contraseña debe tener al menos {PASSWORD_MIN} caracteres.",
                "warning",
            )
            return render_template(
                "auth/reset_confirm.html", password_min=PASSWORD_MIN
            )
        user.set_password(password)
        db.session.commit()
        flash("Contraseña actualizada. Inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_confirm.html", password_min=PASSWORD_MIN)


__all__ = ["reset_bp"]
