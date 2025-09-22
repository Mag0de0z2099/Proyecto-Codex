from __future__ import annotations

# --- ADD: asegurar que el root del proyecto esté en sys.path ---
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
# --- FIN ADD ---

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool


# === Carga la app para tomar la DB URL y el metadata ===
# Soportamos dos ubicaciones comunes de 'db'
def _load_app_and_db():
    from app import create_app

    app = create_app()

    try:
        from app.extensions import db as _db
        db = _db
    except Exception:
        from app import db as _db2
        db = _db2

    return app, db


app, db = _load_app_and_db()
db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
if not db_uri:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI no está definido en la app.")

# Alembic config
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Fuerza a Alembic a usar la misma URL que la app
config.set_main_option("sqlalchemy.url", db_uri)

# Metadata objetivo para autogenerate
target_metadata = getattr(db, "metadata", None) or getattr(db, "Model", None).metadata


def run_migrations_offline() -> None:
    """Modo offline: usa URL literal"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,  # detecta cambios de tipos
        render_as_batch=True,  # seguro para ALTER TABLE en SQLite
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: usa engine/connection"""
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
            render_as_batch=True,  # importante para SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
