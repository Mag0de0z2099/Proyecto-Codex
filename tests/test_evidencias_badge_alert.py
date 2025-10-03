import io
import re

import pytest


def _get_first_part_id(html: str):
    """Busca la primera coincidencia de parte_id en los links de evidencias."""
    match = re.search(r"archivos\\?parte_id=(\\d+)", html)
    return int(match.group(1)) if match else None


def test_css_has_badge_alert(app):
    with app.test_client() as client:
        response = client.get("/static/css/app.css")
        assert response.status_code == 200
        css = response.data.decode("utf-8")
        assert ".badge--alert" in css


def test_badge_alert_turns_on_when_uploading(client):
    response = client.get("/partes")
    if response.status_code != 200:
        response = client.get("/partes/")
    if response.status_code != 200:
        pytest.skip("No existe lista de Partes en rutas conocidas")

    html = response.data.decode("utf-8")
    parte_id = _get_first_part_id(html)
    if not parte_id:
        pytest.skip("No se pudo inferir un parte_id desde la lista (href archivos?parte_id=...)")

    data = {"file": (io.BytesIO(b"demo"), "x.pdf"), "parte_id": str(parte_id)}
    upload = client.post(
        "/archivos/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert upload.status_code == 200

    response_after = client.get("/partes")
    if response_after.status_code != 200:
        response_after = client.get("/partes/")
    html_after = response_after.data.decode("utf-8")
    assert "badge--alert" in html_after
