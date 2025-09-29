from datetime import date


def test_partes_list(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    response = client.get("/partes/")
    assert response.status_code in (200, 302)


def test_partes_create(client, monkeypatch):
    monkeypatch.setenv("DISABLE_SECURITY", "1")
    response = client.post(
        "/partes/new",
        data={
            "fecha": date.today().isoformat(),
            "horas_trabajo": "2.5",
            "actividad": "Excavación",
            "incidencias": "",
            "notas": "prueba",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
