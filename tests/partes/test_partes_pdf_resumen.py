from datetime import date

def test_pdf_parte_smoke(client, monkeypatch):
    from app.extensions import db
    from app.models.parte_diaria import ParteDiaria

    monkeypatch.setenv("DISABLE_SECURITY", "1")
    p = ParteDiaria(fecha=date.today(), horas_trabajo=1.0)
    db.session.add(p)
    db.session.commit()

    r = client.get(f"/partes/{p.id}/pdf")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("application/pdf")


def test_resumen_pdf_smoke(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    r = client.get("/partes/resumen.pdf")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
