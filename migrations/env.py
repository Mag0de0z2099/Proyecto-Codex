from __future__ import with_statement

from logging.config import fileConfig

from alembic import context
from flask import current_app
from sqlalchemy import engine_from_config, pool

# Configuración de logging de Alembic (opcional)
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# >>> AQUI Forzamos a usar el mismo URI que usa Flask <<<
target_metadata = current_app.extensions["migrate"].db.metadata
config.set_main_option("sqlalchemy.url", current_app.config["SQLALCHEMY_DATABASE_URI"])


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
