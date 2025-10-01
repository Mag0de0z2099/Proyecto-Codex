from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, render_template
from sqlalchemy import func

bp_web = Blueprint(
    "web",
    __name__,
    template_folder="templates",
)

from app.db import db
from app.models import Equipo, Operador, ParteDiaria


@bp_web.get("/landing")
def index():
    today = date.today()

    stats = {
        "equipos": 0,
        "operadores": 0,
        "partes_hoy": 0,
        "horas_hoy": 0.0,
    }

    try:
        stats["equipos"] = db.session.query(func.count(Equipo.id)).scalar() or 0
    except Exception:  # pragma: no cover - tablas ausentes en migraciones iniciales
        pass

    try:
        stats["operadores"] = db.session.query(func.count(Operador.id)).scalar() or 0
    except Exception:  # pragma: no cover - tablas ausentes en migraciones iniciales
        pass

    try:
        partes_query = db.session.query(ParteDiaria).filter(ParteDiaria.fecha == today)
        stats["partes_hoy"] = partes_query.count()
        stats["horas_hoy"] = (
            db.session.query(func.coalesce(func.sum(ParteDiaria.horas_trabajo), 0))
            .filter(ParteDiaria.fecha == today)
            .scalar()
            or 0.0
        )
    except Exception:  # pragma: no cover - tablas ausentes
        pass

    return render_template("home.html", stats=stats, today=today)


@bp_web.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@bp_web.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200
