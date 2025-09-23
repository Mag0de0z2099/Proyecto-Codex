import pytest

SAFE_OK = {200, 302}        # público o redirección (por ejemplo a /login)
SAFE_PROTECTED = {401, 403} # rutas que requieren auth (válido en CI)
SAFE_MISSING = {404}        # algunas apps no exponen '/'

# Rutas que evitamos por seguridad o porque no son GET
BLACKLIST_EXACT = {"/static/<path:filename>", "/favicon.ico", "/logout", "/api/assets"}
BLACKLIST_PREFIX = ("/static", "/_debug", "/docs", "/api/")  # ajusta si usas swagger/debug


def get_get_rules(app):
    """Devuelve reglas GET sin parámetros (para poder invocarlas en CI)."""
    rules = []
    for rule in app.url_map.iter_rules():
        if "GET" not in rule.methods:
            continue
        if rule.arguments:           # requiere <id> etc.
            continue
        if rule.rule in BLACKLIST_EXACT:
            continue
        if any(rule.rule.startswith(p) for p in BLACKLIST_PREFIX):
            continue
        rules.append(rule.rule)
    # asegura al menos la raíz
    if "/" not in rules:
        rules.insert(0, "/")
    return sorted(set(rules))


def test_route_returns_non_500(client, app):
    """
    Para cada ruta GET pública, aceptamos:
      - 200/302: ok o redirección
      - 401/403: protegida (válida en CI)
      - 404: raíz inexistente o rutas dinámicas no montadas
    Nunca debe ser 5xx.
    """
    rules = get_get_rules(app)
    if not rules:
        pytest.skip("No hay rutas GET sin parámetros")

    for path in rules:
        res = client.get(path)
        assert res.status_code not in {500, 501, 502, 503, 504}
        assert res.status_code in (SAFE_OK | SAFE_PROTECTED | SAFE_MISSING)
