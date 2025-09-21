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

# Asegúrate de que el paquete principal esté disponible al ejecutar Alembic
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuración de logging de Alembic (opcional)
config = context.config

db_url = os.getenv("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
if db_url:
    # Forzar ssl en Render si no se indicó
    if (
        "sslmode=" not in db_url
        and "localhost" not in db_url
        and "127.0.0.1" not in db_url
    ):
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}sslmode=require"
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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

# >>> AQUI Forzamos a usar el mismo URI que usa Flask <<<
target_metadata = app.extensions["migrate"].db.metadata
config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])


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
