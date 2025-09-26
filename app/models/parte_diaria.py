from __future__ import annotations

from datetime import date, datetime

from app.db import db


class ParteDiaria(db.Model):
    __tablename__ = "partes_diarias"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today, index=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipos.id"), nullable=False, index=True)
    operador_id = db.Column(
        db.Integer,
        db.ForeignKey("operadores.id"),
        nullable=True,
        index=True,
    )
    turno = db.Column(db.String(16), nullable=False, default="matutino")
    ubicacion = db.Column(db.String(128))
    clima = db.Column(db.String(64))
    horas_inicio = db.Column(db.Float)
    horas_fin = db.Column(db.Float)
    horas_trabajadas = db.Column(db.Float)
    combustible_l = db.Column(db.Float)
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    actividades = db.relationship(
        "ActividadDiaria",
        back_populates="parte",
        cascade="all, delete-orphan",
    )
    equipo = db.relationship("Equipo", back_populates="partes")
    operador = db.relationship("Operador", back_populates="partes")

    def calcular_horas_trabajadas(self) -> float | None:
        """Devuelve las horas trabajadas si hay horómetros válidos."""

        if self.horas_inicio is None or self.horas_fin is None:
            return None
        if self.horas_fin < self.horas_inicio:
            return None
        return self.horas_fin - self.horas_inicio

    def actualizar_horas_trabajadas(self) -> None:
        self.horas_trabajadas = self.calcular_horas_trabajadas()

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<ParteDiaria {self.id} equipo={self.equipo_id} fecha={self.fecha}>"


class ActividadDiaria(db.Model):
    __tablename__ = "actividades_diarias"

    id = db.Column(db.Integer, primary_key=True)
    parte_id = db.Column(
        db.Integer,
        db.ForeignKey("partes_diarias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Float)
    unidad = db.Column(db.String(32))
    horas = db.Column(db.Float)
    notas = db.Column(db.String(255))

    parte = db.relationship("ParteDiaria", back_populates="actividades")

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<ActividadDiaria {self.id} parte={self.parte_id}>"
