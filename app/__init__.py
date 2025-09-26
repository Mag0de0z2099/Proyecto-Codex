from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sys
import types


db = SQLAlchemy()
migrate = Migrate()

# Compatibilidad: expone app.db como módulo con la instancia compartida
db_module = types.ModuleType("app.db")
db_module.db = db
sys.modules["app.db"] = db_module


def create_app():
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me")

    db.init_app(app)
    migrate.init_app(app, db)

    # Rutas mínimas
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    # Registrar modelos importando el módulo (para metadata en Alembic)
    from . import models  # noqa: F401

    # Registrar CLI custom
    from .cli import register_cli
    register_cli(app)

    return app
