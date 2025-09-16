"""Extensión de base de datos con SQLAlchemy."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app: Flask) -> None:
    """Inicializar la instancia de :class:`~flask_sqlalchemy.SQLAlchemy`."""

    db.init_app(app)
