from __future__ import with_statement

import atexit
import os
import sys
from contextlib import ExitStack, nullcontext
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from flask import current_app
from sqlalchemy import engine_from_config, pool

# Configuración del archivo de Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asegúrate de que el paquete principal esté disponible al ejecutar Alembic
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url and ("sslmode=" not in url) and ("localhost" not in url) and (
        "127.0.0.1" not in url
    ):
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def _resolve_db_url() -> str:
    # 1) DATABASE_URL de entorno
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return _normalize(env_url)

    # 2) Caer a la config de la app (si existe)
    try:
        from app.config import resolve_db_uri

        app_url = resolve_db_uri()
        if app_url:
            return _normalize(app_url)
    except Exception:
        pass

    # 3) Último recurso: leer alembic.ini (si tuviera url)
    ini_url = config.get_main_option("sqlalchemy.url", "").strip()
    if ini_url:
        return _normalize(ini_url)

    # 4) Sin URL -> error claro
    raise RuntimeError(
        "DATABASE_URL no está definido y alembic.ini no provee sqlalchemy.url"
    )


# Inyecta la URL ANTES de crear el engine
db_url = _resolve_db_url()
config.set_main_option("sqlalchemy.url", db_url)

stack = ExitStack()
atexit.register(stack.close)

try:
    app = current_app._get_current_object()
    ctx = nullcontext()
except RuntimeError:
    from app import create_app

    app = create_app()
    ctx = app.app_context()

stack.enter_context(ctx)

# Usa el metadata del mismo db que configura Flask-Migrate
target_metadata = app.extensions["migrate"].db.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,   # IMPORTANTE para SQLite
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,   # IMPORTANTE para SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
