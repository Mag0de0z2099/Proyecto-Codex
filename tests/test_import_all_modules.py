import importlib
import pkgutil

import pytest

# Módulos que no queremos importar desde tests
SKIP_PREFIXES = (
    "app.migrations",
    "app.static",
    "app.templates",
)
SKIP_EXACT = {
    "app.wsgi",
    "app.manage",
    "app.worker",
}


def iter_modules(base_pkg="app"):
    pkg = importlib.import_module(base_pkg)
    for m in pkgutil.walk_packages(pkg.__path__, prefix=f"{base_pkg}."):
        name = m.name
        if name in SKIP_EXACT or name.startswith(SKIP_PREFIXES):
            continue
        yield name


@pytest.mark.parametrize("modname", list(iter_modules()))
def test_import_module(modname):
    """
    Importar cada submódulo cubre líneas de import y fallará si hay errores graves.
    No ejecuta servidores ni CLI.
    """
    importlib.import_module(modname)
