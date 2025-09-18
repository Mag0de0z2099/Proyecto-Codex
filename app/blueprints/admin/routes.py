from __future__ import annotations

from pathlib import Path
import re

from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user

from app.db import db
from app.models.user import User
from app.security import generate_reset_token

from app.authz import login_required

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
    session_user = session.get("user")
    if session_user:
        return bool(session_user.get("is_admin"))

    return current_user.is_authenticated and getattr(current_user, "is_admin", False)


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

    username = (request.form.get("username") or "").strip()
    email_raw = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    is_admin = request.form.get("is_admin") == "on"
    force_change = request.form.get("force_change") == "on"

    if not username:
        flash("El nombre de usuario es obligatorio.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    if email_raw and not EMAIL_RE.match(email_raw):
        flash("Email inválido.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    if len(password) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    exists_username = User.query.filter_by(username=username).first()
    if exists_username:
        flash("Este nombre de usuario ya está en uso.", "danger")
        return redirect(url_for("admin.admin_new_user"))

    email = email_raw or None
    if email:
        exists_email = db.session.query(User).filter_by(email=email).one_or_none()
        if exists_email:
            flash("Este email ya está registrado.", "danger")
            return redirect(url_for("admin.admin_new_user"))

    u = User(
        username=username,
        email=email,
        is_admin=is_admin,
        force_change_password=force_change,
    )
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

    if not u.email:
        flash("El usuario no tiene email registrado.", "warning")
        return redirect(url_for("admin.admin_users"))

    token = generate_reset_token(u.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    current_app.logger.warning("[ADMIN-RESET] %s -> %s", u.email, reset_url)

    return render_template("admin/reset_link.html", user=u, reset_url=reset_url)


@bp_admin.post("/users/<int:user_id>/toggle-force")
@login_required
def admin_user_toggle_force(user_id: int):
    if not admin_required():
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("web.index"))

    u = db.session.get(User, user_id)
    if not u:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.admin_users"))

    u.force_change_password = not bool(u.force_change_password)
    db.session.commit()
    flash(("Activado" if u.force_change_password else "Desactivado") + " el requisito de cambio de contraseña.", "info")
    return redirect(url_for("admin.admin_users"))
