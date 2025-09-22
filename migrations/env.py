from __future__ import annotations

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

def _load_app_and_db():
    from app import create_app
    app = create_app()

    # Intenta obtener 'db' desde app.extensions o app
    db = None
    try:
        from app.extensions import db as _db
        db = _db
    except Exception:
        try:
            from app import db as _db2
            db = _db2
        except Exception as e:
            raise RuntimeError(
                "No pude importar 'db'. Expón 'db' en app.extensions o en app.__init__"
            ) from e
    return app, db

app, db = _load_app_and_db()
db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
if not db_uri:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI no está definido en la app.")

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Fuerza a Alembic a usar la misma URL que usa la app
config.set_main_option("sqlalchemy.url", db_uri)

target_metadata = getattr(db, "metadata", None) or getattr(db, "Model", None).metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=False,  # En Postgres no hace falta batch mode
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
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
            render_as_batch=False,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
