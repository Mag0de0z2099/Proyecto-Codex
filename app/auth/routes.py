"""Alias de rutas de autenticación para evitar importaciones circulares."""

from __future__ import annotations

from app.blueprints.auth.routes import bp as auth_bp

__all__ = ["auth_bp"]
