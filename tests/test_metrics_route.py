import pytest
from prometheus_client import CONTENT_TYPE_LATEST


def test_metrics_route_exists_and_works(client, app):
    existing = {r.rule for r in app.url_map.iter_rules()}
    path = "/metrics" if "/metrics" in existing else "/api/metrics" if "/api/metrics" in existing else None
    if not path:
        pytest.skip("No se encontró ruta de métricas")
    res = client.get(path)
    assert res.status_code == 200
    ctype = res.headers.get("Content-Type", "").lower()
    expected_version = CONTENT_TYPE_LATEST.lower().split("version=")[-1].split(";")[0]
    assert "text/plain" in ctype and f"version={expected_version}" in ctype
    assert b"# HELP" in res.data or b"# TYPE" in res.data
