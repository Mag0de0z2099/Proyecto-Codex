from flask_migrate import Migrate

migrate = Migrate()


def init_migrations(app, db):
    """Inicializar el soporte de migraciones en la aplicación."""
    # Vincula Flask-Migrate/Alembic a la app y al objeto db
    migrate.init_app(app, db)
