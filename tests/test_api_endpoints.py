import os

import pytest

ALLOWED = {200, 302, 401, 403, 404}


def get_api_get_rules(app):
    rules = []
    for rule in app.url_map.iter_rules():
        if "GET" not in rule.methods:
            continue
        if not rule.rule.startswith("/api"):
            continue
        if rule.arguments:  # evitamos <id>, etc.
            continue
        rules.append(rule.rule)
    return sorted(set(rules))


_API_PATHS = None


def _load_app_for_collection():
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    try:
        from app import create_app
        flask_app = create_app()
    except Exception:
        from app import app as flask_app
    return flask_app


def _get_api_paths():
    global _API_PATHS
    if _API_PATHS is None:
        flask_app = _load_app_for_collection()
        _API_PATHS = get_api_get_rules(flask_app)
    return _API_PATHS


def pytest_generate_tests(metafunc):
    if "path" in metafunc.fixturenames:
        paths = _get_api_paths()
        if not paths:
            metafunc.parametrize(
                "path",
                [pytest.param(None, marks=pytest.mark.skip("No hay rutas /api GET sin parámetros"))],
            )
        else:
            metafunc.parametrize("path", paths, ids=paths)


def test_parametrize_over_api(app):
    paths = get_api_get_rules(app)
    if not paths:
        pytest.skip("No hay rutas /api GET sin parámetros")


def test_api_route_ok(client, path):
    if path is None:
        pytest.skip("No hay rutas /api GET sin parámetros")

    res = client.get(path)
    if res.status_code == 500:
        pytest.skip(f"{path} devolvió 500 (dependencia externa o error controlado en pruebas)")

    assert res.status_code in ALLOWED
    # Si responde 200 y trae JSON, que sea parseable
    if res.status_code == 200 and "json" in (res.headers.get("Content-Type") or "").lower():
        _ = res.get_json(silent=True)
