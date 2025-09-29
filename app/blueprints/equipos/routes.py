from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from sqlalchemy import or_
from app.extensions import db

# Importa tu modelo
try:
    from app.models.equipo import Equipo  # si lo tienes separado
except Exception:
    from app.models import Equipo          # o todo en models/__init__.py

bp = Blueprint("equipos", __name__, url_prefix="/equipos", template_folder="../../templates/equipos")

# --- Bypass de guard si en algún momento había before_request ---
@bp.before_request
def _guard():
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return

# --- Lista + búsqueda + paginación ---
@bp.get("/")
def index():
    q = (request.args.get("q") or "").strip()
    page = int(request.args.get("page") or 1)
    per_page = 10

    query = Equipo.query
    if q:
        # Ajusta los campos si tu modelo usa otros (p.ej. nombre, descripcion, serie)
        filters = []
        for field in ("nombre", "descripcion", "serie"):
            if hasattr(Equipo, field):
                filters.append(getattr(Equipo, field).ilike(f"%{q}%"))
        if filters:
            query = query.filter(or_(*filters))

    pagination = query.order_by(Equipo.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("equipos/index.html", pagination=pagination, rows=pagination.items, q=q)

# --- Crear ---
@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        # Ajusta nombres de campos según tu modelo
        data = {
            "nombre": request.form.get("nombre", "").strip(),
            "descripcion": request.form.get("descripcion", "").strip(),
            "serie": request.form.get("serie", "").strip(),
            "estatus": request.form.get("estatus", "").strip() or "activo",
        }
        # filtra claves que realmente existen en tu modelo
        payload = {}
        for k, v in data.items():
            if hasattr(Equipo, k) and v is not None:
                payload[k] = v

        e = Equipo(**payload)
        db.session.add(e)
        db.session.commit()
        flash("Equipo creado", "success")
        return redirect(url_for("equipos.index"))

    return render_template("equipos/form.html", item=None)

# --- Editar ---
@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    item = Equipo.query.get_or_404(id)
    if request.method == "POST":
        for k in ("nombre", "descripcion", "serie", "estatus"):
            if hasattr(item, k) and k in request.form:
                setattr(item, k, (request.form.get(k) or "").strip())
        db.session.commit()
        flash("Equipo actualizado", "success")
        return redirect(url_for("equipos.index"))
    return render_template("equipos/form.html", item=item)

# --- Borrar ---
@bp.post("/<int:id>/delete")
def delete(id):
    item = Equipo.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Equipo eliminado", "success")
    return redirect(url_for("equipos.index"))
