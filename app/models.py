"""Modelos de base de datos de la aplicación."""

from __future__ import annotations

from datetime import datetime

from .db import db


class Todo(db.Model):
    """Modelo sencillo para tareas pendientes."""

    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, object]:
        """Representar la tarea como diccionario serializable."""

        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "created_at": self.created_at.isoformat(),
        }
