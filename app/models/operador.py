from __future__ import annotations

from datetime import date

from app.extensions import db


class Operador(db.Model):
    __tablename__ = "operadores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(160), nullable=False)
    doc_id = db.Column(db.String(80))
    licencia_vence = db.Column(db.Date)
    notas = db.Column(db.Text)
    estatus = db.Column(db.String(32), default="activo")

    partes = db.relationship(
        "ParteDiaria",
        back_populates="operador",
        lazy="dynamic",
    )

    def dias_para_vencer(self) -> int | None:
        if not self.licencia_vence:
            return None
        return (self.licencia_vence - date.today()).days
