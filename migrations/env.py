import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url and ("sslmode=" not in url) and ("localhost" not in url) and ("127.0.0.1" not in url):
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


def _resolve_db_url() -> str:
    # 1) Environment
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return _normalize(env_url)
    # 2) App config (si existe)
    try:
        from app.config import resolve_db_uri

        app_url = resolve_db_uri()
        if app_url:
            return _normalize(app_url)
    except Exception:
        pass
    # 3) alembic.ini (último recurso)
    ini_url = (config.get_main_option("sqlalchemy.url", "") or "").strip()
    if ini_url:
        return _normalize(ini_url)
    raise RuntimeError("No DB URL: define DATABASE_URL o sqlalchemy.url en alembic.ini")


db_url = _resolve_db_url()
config.set_main_option("sqlalchemy.url", db_url)  # *** CRÍTICO: antes de engine_from_config ***

import atexit
import sys
from contextlib import ExitStack, nullcontext
from pathlib import Path

from flask import current_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
