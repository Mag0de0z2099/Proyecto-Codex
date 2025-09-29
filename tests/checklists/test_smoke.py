from datetime import date


def test_templates_index(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    r = client.get("/checklists/templates")
    assert r.status_code in (200, 302)


def test_run_pdf_smoke(client, monkeypatch):
    from app.extensions import db
    from app.models.checklist import (
        ChecklistTemplate,
        ChecklistItem,
        ChecklistRun,
        ChecklistAnswer,
    )

    monkeypatch.setenv("DISABLE_SECURITY", "1")
    t = ChecklistTemplate(nombre="NOM-017", norma="NOM-017-STPS")
    db.session.add(t)
    db.session.flush()
    db.session.add(
        ChecklistItem(template_id=t.id, texto="Trae casco", tipo="bool", orden=1)
    )
    db.session.commit()
    run = ChecklistRun(template_id=t.id, fecha=date.today(), pct_ok=100.0)
    db.session.add(run)
    db.session.flush()
    db.session.add(
        ChecklistAnswer(
            run_id=run.id,
            item_id=t.items.first().id,
            valor_bool=True,
        )
    )
    db.session.commit()
    r = client.get(f"/checklists/run/{run.id}/pdf")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/pdf")
