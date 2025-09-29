from flask import Blueprint, current_app, render_template
from sqlalchemy import func

from app.extensions import db

bp = Blueprint(
    "dashboard_bp",
    __name__,
    url_prefix="/dashboard",
    template_folder="../../templates/dashboard",
)


@bp.before_request
def _guard():
    if current_app.config.get("SECURITY_DISABLED") or current_app.config.get("LOGIN_DISABLED"):
        return


@bp.get("/")
def index():
    counts: dict[str, int | str] = {}

    def safe_count(model, label: str) -> None:
        try:
            counts[label] = db.session.query(func.count(model.id)).scalar() or 0
        except Exception:  # pragma: no cover - conteo defensivo
            counts[label] = "-"

    try:
        from app.models.equipo import Equipo
    except Exception:  # pragma: no cover - fallback para apps sin módulo
        from app.models import Equipo

    try:
        from app.models.operador import Operador
    except Exception:  # pragma: no cover - fallback para apps sin módulo
        from app.models import Operador

    try:
        from app.models.parte_diaria import ParteDiaria
    except Exception:  # pragma: no cover - proyectos sin partes
        ParteDiaria = None

    try:
        from app.models.checklist import ChecklistRun, ChecklistTemplate
    except Exception:  # pragma: no cover - proyectos sin checklists
        ChecklistTemplate = ChecklistRun = None

    try:
        from app.models.parte_diaria import ArchivoAdjunto
    except Exception:  # pragma: no cover - apps con modelo alterno
        try:
            from app.models.archivo import ArchivoAdjunto
        except Exception:  # pragma: no cover - sin archivos
            ArchivoAdjunto = None

    for model, label in [
        (Equipo, "equipos"),
        (Operador, "operadores"),
        (ParteDiaria, "partes"),
        (ChecklistTemplate, "plantillas"),
        (ChecklistRun, "checklist_runs"),
        (ArchivoAdjunto, "archivos"),
    ]:
        if model is not None:
            safe_count(model, label)
        else:
            counts[label] = "-"

    return render_template("dashboard/index.html", counts=counts)
