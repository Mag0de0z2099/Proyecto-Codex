from __future__ import annotations

import re
from functools import wraps
from pathlib import Path

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
from flask_login import login_required as flask_login_required

from app.db import db
from app.models import Folder, MetricDaily, Project, User
from app.security import generate_reset_token
from app.auth.roles import ROLES, admin_required

bp_admin = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    decorated = flask_login_required(view)

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_app.config.get("AUTH_SIMPLE", True):
            if session.get("user"):
                return view(*args, **kwargs)
            return redirect(url_for("auth.login", next=request.path))
        return decorated(*args, **kwargs)

    return wrapped


@bp_admin.get("/")
@login_required
@admin_required
def index():
    projects = Project.query.all()
    total_projects = len(projects)
    avg_progress = (
        round(sum(p.progress for p in projects) / total_projects, 1)
        if total_projects
        else 0.0
    )
    budget = sum(p.budget for p in projects)
    spent = sum(p.spent for p in projects)
    proj = projects[0] if projects else None
    return render_template(
        "admin/index.html",
        projects=projects,
        total_projects=total_projects,
        avg_progress=avg_progress,
        budget=budget,
        spent=spent,
        main_project=proj,
    )


@bp_admin.get("/kpi/<int:project_id>.json")
@login_required
@admin_required
def kpi_json(project_id: int):
    rows = (
        MetricDaily.query.filter_by(project_id=project_id)
        .order_by(MetricDaily.date)
        .all()
    )
    labels = [r.date.isoformat() for r in rows if r.kpi_name == "progreso"]
    progreso = [r.value for r in rows if r.kpi_name == "progreso"]
    gasto = [r.value for r in rows if r.kpi_name == "gasto"]
    return jsonify({"labels": labels, "progreso": progreso, "gasto": gasto})


@bp_admin.get("/folders")
@login_required
@admin_required
def folders_list():
    folders = Folder.query.order_by(Folder.created_at.desc()).all()
    projects = Project.query.all()
    return render_template(
        "admin/folders_list.html", folders=folders, projects=projects
    )


@bp_admin.post("/folders")
@login_required
@admin_required
def folders_create():
    project_id = request.form.get("project_id")
    name = (request.form.get("name") or "").strip()
    if not project_id or not name:
        flash("Proyecto y nombre son obligatorios.", "warning")
        return redirect(url_for("admin.folders_list"))

    folder = Folder(project_id=int(project_id), name=name, created_by="admin")
    db.session.add(folder)
    db.session.commit()
    flash("Carpeta creada.", "success")
    return redirect(url_for("admin.folders_list"))


@bp_admin.get("/files")
@login_required
@admin_required
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
@bp_admin.get("/users/new")
@login_required
@admin_required
def admin_new_user():
    return render_template("admin/new_user.html")


@bp_admin.post("/users/new")
@login_required
@admin_required
def admin_create_user():

    username = (request.form.get("username") or "").strip()
    email_raw = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    is_admin_flag = request.form.get("is_admin") == "on"
    role_input = (request.form.get("role") or "").strip().lower()
    title_raw = (request.form.get("title") or "").strip()
    role = role_input if role_input in ROLES else "viewer"
    if is_admin_flag:
        role = "admin"
    is_admin = role == "admin"
    title = title_raw or None
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

    user = User(
        username=username,
        email=email,
        role=role,
        title=title,
        is_admin=is_admin,
        force_change_password=force_change,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Usuario creado correctamente.", "success")
    return redirect(url_for("admin.index"))


@bp_admin.get("/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users)


@bp_admin.post("/users/<int:user_id>/reset-link")
@login_required
@admin_required
def admin_user_reset_link(user_id: int):

    user = db.session.get(User, user_id)
    if not user:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.admin_users"))

    if not user.email:
        flash("El usuario no tiene email registrado.", "warning")
        return redirect(url_for("admin.admin_users"))

    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    current_app.logger.warning("[ADMIN-RESET] %s -> %s", user.email, reset_url)

    return render_template("admin/reset_link.html", user=user, reset_url=reset_url)


@bp_admin.post("/users/<int:user_id>/toggle-force")
@login_required
@admin_required
def admin_user_toggle_force(user_id: int):

    user = db.session.get(User, user_id)
    if not user:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.admin_users"))

    user.force_change_password = not bool(user.force_change_password)
    db.session.commit()
    flash(
        ("Activado" if user.force_change_password else "Desactivado")
        + " el requisito de cambio de contraseña.",
        "info",
    )
    return redirect(url_for("admin.admin_users"))
