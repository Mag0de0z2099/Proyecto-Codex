from __future__ import annotations

from pathlib import Path
import re

from flask import current_app, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from app.db import db
from app.models.user import User
from app.security import generate_reset_token

from . import bp_admin


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp_admin.get("/")
@login_required
def index():
    return render_template("admin/index.html")


@bp_admin.get("/files")
@login_required
def list_files():
    data_dir = Path(current_app.config["DATA_DIR"])
    items: list[dict[str, object]] = []

    for path in sorted(data_dir.glob("**/*")):
        relative = path.relative_to(data_dir).as_posix()
        items.append(
            {
                "name": relative,
                "is_dir": path.is_dir(),
                "size": path.stat().st_size if path.is_file() else None,
            }
        )

    return render_template("admin/files.html", items=items, base=str(data_dir))


def admin_required() -> bool:
    return current_user.is_authenticated and current_user.is_admin


@bp_admin.get("/users/new")
@login_required
def admin_new_user():
    if not admin_required():
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("web.index"))
    return render_template("admin/new_user.html")


@bp_admin.post("/users/new")
@login_required
def admin_create_user():
    if not admin_required():
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("web.index"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    is_admin = request.form.get("is_admin") == "on"

    if not EMAIL_RE.match(email):
        flash("Email inválido.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    if len(password) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    exists = db.session.query(User).filter_by(email=email).one_or_none()
    if exists:
        flash("Este email ya está registrado.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    u = User(email=email, is_admin=is_admin)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash("Usuario creado correctamente.", "success")
    return redirect(url_for("admin.index"))


@bp_admin.get("/users")
@login_required
def admin_users():
    if not admin_required():
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("web.index"))
    q = User.query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=q)


@bp_admin.post("/users/<int:user_id>/reset-link")
@login_required
def admin_user_reset_link(user_id: int):
    if not admin_required():
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("web.index"))

    u = db.session.get(User, user_id)
    if not u:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.admin_users"))

    token = generate_reset_token(u.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    current_app.logger.warning("[ADMIN-RESET] %s -> %s", u.email, reset_url)

    return render_template("admin/reset_link.html", user=u, reset_url=reset_url)
