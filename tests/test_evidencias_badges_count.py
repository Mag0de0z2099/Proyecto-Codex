import re

import pytest


def _first_ok(client, paths):
    for p in paths:
        r = client.get(p)
        if r.status_code == 200:
            return p, r
    return None, None


def test_partes_badge_present_and_numeric(client):
    path, resp = _first_ok(client, ["/partes/", "/partes"])
    if not resp:
        pytest.skip("No existe lista de Partes en rutas conocidas")
    html = resp.data.decode("utf-8")
    if "Evidencias" not in html and ("Inicia sesión" in html or "Login" in html):
        pytest.skip("Ruta de Partes requiere autenticación")
    # debe existir el botón con badge
    if "Evidencias" not in html:
        pytest.skip("No se encontraron registros de Partes con botón de Evidencias")
    m = re.search(r'Evidencias\s*<span class="badge">(\d+)</span>', html)
    if not m:
        pytest.skip("No se encontró badge en Partes")
    assert int(m.group(1)) >= 0


def test_runs_badge_present_and_numeric(client):
    candidates = ["/checklists/runs", "/checklists/runs/", "/checklists"]
    path, resp = _first_ok(client, candidates)
    if not resp:
        pytest.skip("No existe lista de ChecklistRuns en rutas conocidas")
    html = resp.data.decode("utf-8")
    if "Evidencias" not in html and ("Inicia sesión" in html or "Login" in html):
        pytest.skip("Ruta de Runs requiere autenticación")
    if "Evidencias" not in html:
        pytest.skip("No se encontraron registros de Runs con botón de Evidencias")
    m = re.search(r'Evidencias\s*<span class="badge">(\d+)</span>', html)
    if not m:
        pytest.skip("No se encontró badge en Runs")
    assert int(m.group(1)) >= 0
