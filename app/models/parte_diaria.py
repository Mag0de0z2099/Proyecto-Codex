from __future__ import annotations

from datetime import date

from app.extensions import db


class ParteDiaria(db.Model):
    __tablename__ = "partes_diarias"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)

    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=True)
    operador_id = db.Column(db.Integer, db.ForeignKey("operadores.id"), nullable=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey("checklists.id"), nullable=True)

    horas_trabajo = db.Column(db.Float, nullable=False, default=0)
    actividad = db.Column(db.Text)
    incidencias = db.Column(db.Text)
    notas = db.Column(db.Text)

    equipo = db.relationship("Equipo", back_populates="partes")
    operador = db.relationship("Operador", back_populates="partes")

    def __repr__(self) -> str:  # pragma: no cover - ayuda para depuración
        return f"<ParteDiaria id={self.id} fecha={self.fecha}>"


class ArchivoAdjunto(db.Model):
    __tablename__ = "archivos"

    id = db.Column(db.Integer, primary_key=True)
    tabla = db.Column(db.String(64), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    subido_en = db.Column(db.DateTime, server_default=db.func.now())
