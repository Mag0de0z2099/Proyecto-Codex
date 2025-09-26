from __future__ import annotations

from datetime import datetime

from app.db import db


class Equipo(db.Model):
    __tablename__ = "equipos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(64), unique=True, nullable=False, index=True)
    tipo = db.Column(db.String(64), nullable=False)
    marca = db.Column(db.String(64))
    modelo = db.Column(db.String(64))
    serie = db.Column(db.String(128))
    placas = db.Column(db.String(32))
    status = db.Column(db.String(32), default="activo")
    ubicacion = db.Column(db.String(128))
    horas_uso = db.Column(db.Float, default=0.0)
    fecha_alta = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
