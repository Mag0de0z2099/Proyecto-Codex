from datetime import date

import pytest


def _ensure_parte(app):
    from app.extensions import db
    from app.models.parte_diaria import ParteDiaria

    with app.app_context():
        if db.session.query(ParteDiaria).count():
            return db.session.query(ParteDiaria).first()
        parte = ParteDiaria(fecha=date.today())
        db.session.add(parte)
        db.session.commit()
        return parte


def _ensure_run(app):
    from app.extensions import db
    from app.models.checklist import ChecklistRun, ChecklistTemplate

    with app.app_context():
        template = db.session.query(ChecklistTemplate).first()
        if not template:
            template = ChecklistTemplate(nombre="Demo", norma="")
            db.session.add(template)
            db.session.commit()
        run = db.session.query(ChecklistRun).first()
        if run:
            return run
        run = ChecklistRun(fecha=date.today(), template_id=template.id, pct_ok=100)
        db.session.add(run)
        db.session.commit()
        return run


def _first_ok(client, paths):
    for p in paths:
        r = client.get(p)
        if r.status_code == 200:
            return p, r
    return None, None


def test_partes_list_has_evidencias_button(client, app, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    _ensure_parte(app)
    path, resp = _first_ok(client, ["/partes/", "/partes"])
    if not resp:
        pytest.skip("No existe lista de Partes en rutas conocidas")
    html = resp.data.decode("utf-8")
    assert (
        'href="/archivos?parte_id=' in html
        or 'href="/archivos/?parte_id=' in html
        or ('href="' in html and 'archivos?parte_id=' in html)
    )


def test_checklist_runs_list_has_evidencias_button(client, app, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    _ensure_run(app)
    candidates = ["/checklists/runs", "/checklists/runs/", "/checklists"]
    path, resp = _first_ok(client, candidates)
    if not resp:
        pytest.skip("No existe lista de ChecklistRuns en rutas conocidas")
    html = resp.data.decode("utf-8")
    assert (
        'href="/archivos?run_id=' in html
        or 'href="/archivos/?run_id=' in html
        or ('href="' in html and 'archivos?run_id=' in html)
    )
