"""Punto de entrada WSGI conservado por compatibilidad."""

from __future__ import annotations

from . import create_app

# Usa ``gunicorn wsgi:app`` en producción; este módulo queda disponible
# para procesos auxiliares o tooling que aún dependan de ``app.main:app``.
app = create_app()
