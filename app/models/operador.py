from __future__ import annotations

from datetime import datetime

from app.db import db


class Operador(db.Model):
    __tablename__ = "operadores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, index=True)
    identificacion = db.Column(db.String(64), unique=True)
    licencia = db.Column(db.String(64))
    puesto = db.Column(db.String(64))
    telefono = db.Column(db.String(32))
    status = db.Column(db.String(32), default="activo")
    fecha_alta = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
