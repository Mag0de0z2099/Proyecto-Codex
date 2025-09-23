import pytest

CANDIDATES = [
    "/api/health",
    "/api/ping",
    "/health",
    "/metrics",   # si usas Prometheus
    "/",          # home
]


def test_any_known_candidate_responds(client, app):
    """
    Si la app tiene alguna ruta de salud conocida, que no truene.
    No falla si ninguna existe: en ese caso se marca como salto.
    """
    # mapa para saber cuáles existen
    existing = {r.rule for r in app.url_map.iter_rules()}
    tested_any = False
    for path in CANDIDATES:
        if path not in existing:
            continue
        tested_any = True
        res = client.get(path)
        assert res.status_code < 500  # no debe tronar
    if not tested_any:
        pytest.skip("No se encontraron rutas candidatas de salud/ping/raíz")
