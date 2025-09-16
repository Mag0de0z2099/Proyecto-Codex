"""Punto de entrada para servidores WSGI como gunicorn."""

from __future__ import annotations

from . import create_app

# Render arranca con: ``gunicorn app.main:app --bind 0.0.0.0:$PORT``
app = create_app()
