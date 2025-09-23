import pytest

# Ajusta la lista a lo que tengas disponible
CANDIDATES = [
    "/auth/login",
    "/auth/signup",
    "/logout",        # puede redirigir -> 302
    "/api/health",
    "/api/ping",
    "/metrics",       # si expones Prometheus
]


@pytest.mark.parametrize("path", CANDIDATES)
def test_candidates_get(client, app, path):
    existing = {r.rule for r in app.url_map.iter_rules()}
    if path not in existing:
        pytest.skip(f"{path} no existe")
    res = client.get(path)
    assert res.status_code in (200, 302, 401, 403)
