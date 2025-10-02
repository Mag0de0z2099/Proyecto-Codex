from __future__ import annotations

import io
import re


def test_upload_download_delete_flow(client, app):
    data = {"file": (io.BytesIO(b"demo"), "prueba.pdf")}
    response = client.post(
        "/archivos/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get("/archivos/")
    assert response.status_code == 200
    html = response.data.decode()
    assert "prueba.pdf" in html

    match = re.search(r"/archivos/(\d+)/download", html)
    assert match, "no se encontró enlace de descarga"
    attachment_id = int(match.group(1))

    response = client.get(f"/archivos/{attachment_id}/download")
    assert response.status_code == 200
    assert response.data == b"demo"

    response = client.post(
        f"/archivos/{attachment_id}/delete",
        follow_redirects=True,
        data={},
    )
    assert response.status_code == 200
