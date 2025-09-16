from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.sql import expression

from ..db import db


class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    completed = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=expression.false(),
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
