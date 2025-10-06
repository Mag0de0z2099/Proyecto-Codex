from __future__ import annotations

import os
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from sqlalchemy.exc import IntegrityError

from app.db import db
from app.models import Bitacora, Folder, MetricDaily, Project, User
from app.auth.roles import ROLES, admin_required, role_required
from app.utils.rbac import require_roles, require_approved
from app.utils.validators import is_valid_email
from app.security import generate_reset_token
from app.security.authz import require_login
from app.services.user_service import list_users as service_list_users

bp_admin = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")

@bp_admin.app_context_processor
def _admin_template_helpers():
    def admin_url(primary: str, fallback: str | None = None) -> str:
        for endpoint in (primary, fallback):
            if endpoint and endpoint in current_app.view_functions:
                try:
                    return url_for(endpoint)
                except Exception:
                    continue
        return "#"

    def has_admin_endpoint(endpoint: str) -> bool:
        return endpoint in current_app.view_functions

    return {"admin_url": admin_url, "has_admin_endpoint": has_admin_endpoint}
@bp_admin.get("/")
@require_login
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
    ultimas_logs = (
        Bitacora.query.order_by(Bitacora.created_at.desc()).limit(5).all()
    )
    return render_template(
        "admin/index.html",
        total_projects=total_projects,
        avg_progress=avg_progress,
        budget=budget,
        spent=spent,
        ultimas=ultimas_logs,
        projects=projects,
    )


bp_admin.add_url_rule("/", view_func=index, endpoint="dashboard")


@bp_admin.get("/kpi/<int:project_id>.json")
@require_login
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


# PROYECTOS (listar/crear rápido)
@bp_admin.get("/projects")
@require_login
@role_required("admin", "supervisor")
def projects():
    data = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=data)


@bp_admin.post("/projects")
@require_login
@role_required("admin", "supervisor")
def projects_create():
    payload = request.get_json(silent=True)
    is_json = isinstance(payload, dict)
    data = payload if is_json else request.form

    name = (data.get("name") or "").strip()
    client = (data.get("client") or "").strip()

    if not name:
        if is_json:
            return (
                jsonify({"ok": False, "error": "El nombre es obligatorio."}),
                400,
            )
        flash("Nombre de proyecto requerido", "warning")
        return redirect(url_for("admin.projects"))

    if Project.query.filter_by(name=name).first():
        if is_json:
            return (
                jsonify({"ok": False, "error": "Ya existe un proyecto con ese nombre."}),
                409,
            )
        flash("Ya existe un proyecto con ese nombre.", "warning")
        return redirect(url_for("admin.projects"))

    project = Project(
        name=name,
        client=client or None,
        status="activo",
        progress=0.0,
        budget=0.0,
        spent=0.0,
    )
    db.session.add(project)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(
            "Duplicate project creation attempt", extra={"name": name}
        )
        if is_json:
            return (
                jsonify({"ok": False, "error": "Ya existe un proyecto con ese nombre."}),
                409,
            )
        flash("Ya existe un proyecto con ese nombre.", "warning")
        return redirect(url_for("admin.projects"))

    if is_json:
        return (
            jsonify({"ok": True, "project": {"id": project.id, "name": project.name}}),
            201,
        )

    flash("Proyecto creado", "success")
    return redirect(url_for("admin.projects"))


# BITÁCORAS (listar/crear)
@bp_admin.get("/bitacoras")
@require_login
@role_required("admin", "supervisor", "editor")
def bitacoras():
    logs = (
        Bitacora.query.order_by(Bitacora.date.desc(), Bitacora.created_at.desc())
        .limit(50)
        .all()
    )
    projects = Project.query.order_by(Project.name).all()
    return render_template(
        "admin/bitacoras.html",
        logs=logs,
        projects=projects,
        default_date=date.today().isoformat(),
    )


@bp_admin.post("/bitacoras")
@require_login
@role_required("admin", "supervisor", "editor")
def bitacoras_create():
    project_id = request.form.get("project_id")
    if not project_id:
        flash("Selecciona un proyecto", "warning")
        return redirect(url_for("admin.bitacoras"))
    try:
        project_id_int = int(project_id)
    except (TypeError, ValueError):
        flash("Proyecto inválido", "warning")
        return redirect(url_for("admin.bitacoras"))
    author = request.form.get("author", "")
    text = request.form.get("text", "")
    date_input = request.form.get("date")
    try:
        log_date = date.fromisoformat(date_input) if date_input else date.today()
    except ValueError:
        log_date = date.today()
    bitacora = Bitacora(
        project_id=project_id_int,
        author=author or "sistema",
        text=text,
        date=log_date,
    )
    db.session.add(bitacora)
    db.session.commit()
    flash("Bitácora registrada", "success")
    return redirect(url_for("admin.bitacoras"))


@bp_admin.get("/folders")
@require_login
@admin_required
def folders_list():
    folders = Folder.query.order_by(Folder.created_at.desc()).all()
    projects = Project.query.all()
    return render_template(
        "admin/folders_list.html", folders=folders, projects=projects
    )


@bp_admin.post("/folders")
@require_login
@admin_required
def folders_create():
    project_id = request.form.get("project_id")
    logical_path = (request.form.get("logical_path") or "").strip()
    fs_path_raw = (request.form.get("fs_path") or "").strip()
    if not project_id or not logical_path or not fs_path_raw:
        flash("Proyecto, ruta lógica y ruta física son obligatorios.", "warning")
        return redirect(url_for("admin.folders_list"))

    folder = Folder(
        project_id=int(project_id),
        logical_path=logical_path,
        fs_path=os.path.abspath(fs_path_raw),
    )
    db.session.add(folder)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            "Ya existe una carpeta con esa ruta lógica para el proyecto.",
            "warning",
        )
    else:
        flash("Carpeta creada.", "success")
    return redirect(url_for("admin.folders_list"))


@bp_admin.get("/files")
@require_login
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
@require_login
@require_approved
@admin_required
@require_roles("admin")
def admin_new_user():
    return render_template("admin/new_user.html")


@bp_admin.post("/users/new")
@require_login
@require_approved
@admin_required
@require_roles("admin")
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

    if email_raw and not is_valid_email(email_raw):
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

    category_raw = request.form.get("category") or None
    category_value = category_raw.strip() if category_raw else None

    user = User(
        username=username,
        email=email,
        role=role,
        title=title,
        is_admin=is_admin,
        force_change_password=force_change,
        status="approved",
        category=category_value,
        is_active=True,
        approved_at=datetime.now(timezone.utc),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Usuario creado correctamente.", "success")
    return redirect(url_for("admin.index"))


# --- Gestión de usuarios (solo admin) ---


@bp_admin.get("/users/pending")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def users_pending():
    users_q = (
        User.query.filter(User.status == "pending")
        .order_by(User.created_at.asc())
        .all()
    )
    return render_template("admin/users_pending.html", users=users_q)


@bp_admin.post("/users/<int:user_id>/approve")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def approve_user(user_id: int):
    user = User.query.get_or_404(user_id)
    role = (request.form.get("role") or "viewer").strip().lower()
    category_raw = request.form.get("category") or None
    category = category_raw.strip() if category_raw else None
    if role not in ROLES:
        role = "viewer"
    user.status = "approved"
    user.role = role
    user.category = category
    user.is_admin = role == "admin"
    user.is_active = True
    user.approved_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"Usuario {user.username} aprobado.", "success")
    return redirect(url_for("admin.users_pending"))


@bp_admin.post("/users/<int:user_id>/reject")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def reject_user(user_id: int):
    user = User.query.get_or_404(user_id)
    user.status = "rejected"
    user.is_active = False
    user.approved_at = None
    db.session.commit()
    flash(f"Usuario {user.username} rechazado.", "info")
    return redirect(url_for("admin.users_pending"))


@bp_admin.get("/users")
@require_login
@require_approved
@require_roles("admin", "supervisor")
@role_required("admin", "supervisor")
def users():
    status = request.args.get("status") or ""
    search = request.args.get("q", "")

    def _parse(value: str | None, default: int, minimum: int = 1, maximum: int = 100) -> int:
        try:
            parsed = int(value) if value else default
        except (TypeError, ValueError):
            return default
        if parsed < minimum:
            parsed = minimum
        if parsed > maximum:
            parsed = maximum
        return parsed

    page = _parse(request.args.get("page"), 1)
    per_page = _parse(request.args.get("per_page"), 20, minimum=5, maximum=100)

    try:
        rows, meta = service_list_users(
            status=status or None,
            search=search or None,
            page=page,
            per_page=per_page,
        )
    except Exception:
        rows = []
        meta = {"page": page, "per_page": per_page, "pages": 1, "total": 0}

    roles = list(ROLES)
    return render_template(
        "admin/users.html",
        users=rows,
        ROLES=roles,
        meta=meta,
        q=search,
        status=status,
    )


@bp_admin.post("/users/role")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def users_set_role():
    user_id = int(request.form["user_id"])
    role = request.form["role"]
    user = User.query.get_or_404(user_id)
    if role not in ROLES:
        flash("Rol inválido", "warning")
        return redirect(url_for("admin.users"))
    user.role = role
    user.is_admin = role == "admin"
    db.session.commit()
    flash(f"Rol de {user.username} → {role}", "success")
    return redirect(url_for("admin.users"))


@bp_admin.post("/users/toggle")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def users_toggle_active():
    user_id = int(request.form["user_id"])
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(
        f"Estado de {user.username} → {'activo' if user.is_active else 'inactivo'}",
        "success",
    )
    return redirect(url_for("admin.users"))


@bp_admin.post("/users/<int:user_id>/reset-link")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def admin_user_reset_link(user_id: int):

    user = db.session.get(User, user_id)
    if not user:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.users"))

    if not user.email:
        flash("El usuario no tiene email registrado.", "warning")
        return redirect(url_for("admin.users"))

    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    current_app.logger.warning("[ADMIN-RESET] %s -> %s", user.email, reset_url)

    return render_template("admin/reset_link.html", user=user, reset_url=reset_url)


@bp_admin.post("/users/<int:user_id>/toggle-force")
@require_login
@require_approved
@admin_required
@require_roles("admin")
def admin_user_toggle_force(user_id: int):

    user = db.session.get(User, user_id)
    if not user:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("admin.users"))

    user.force_change_password = not bool(user.force_change_password)
    db.session.commit()
    flash(
        ("Activado" if user.force_change_password else "Desactivado")
        + " el requisito de cambio de contraseña.",
        "info",
    )
    return redirect(url_for("admin.users"))
