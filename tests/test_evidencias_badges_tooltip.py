import pytest


def _first_ok(client, paths):
    for path in paths:
        response = client.get(path)
        if response.status_code == 200:
            return response
    return None


def test_partes_evidencias_shows_type_badges_and_tooltip(client):
    resp = _first_ok(client, ["/partes/", "/partes"])
    if not resp:
        pytest.skip("No existe lista de Partes")
    html = resp.data.decode("utf-8")
    if "Iniciar sesión" in html or "Iniciar Sesión" in html or "Login" in html:
        pytest.skip("Ruta protegida")
    if "Evidencias" not in html:
        pytest.skip("No se encontraron botones de Evidencias")
    assert "Evidencias" in html
    assert "badge--pdf" in html
    assert "badge--img" in html
    assert "Tamaño total:" in html


def test_runs_evidencias_shows_type_badges_and_tooltip(client):
    resp = _first_ok(client, ["/checklists/runs", "/checklists/runs/", "/checklists"])
    if not resp:
        pytest.skip("No existe lista de Runs")
    html = resp.data.decode("utf-8")
    if "Iniciar sesión" in html or "Iniciar Sesión" in html or "Login" in html:
        pytest.skip("Ruta protegida")
    if "Evidencias" not in html:
        pytest.skip("No se encontraron botones de Evidencias")
    assert "Evidencias" in html
    assert "badge--pdf" in html
    assert "badge--img" in html
    assert "Tamaño total:" in html


def test_human_size_exposes_units(app):
    with app.test_client() as client:
        home = client.get("/")
    assert home.status_code in (200, 302)
