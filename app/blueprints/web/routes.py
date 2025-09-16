"""Rutas web del proyecto."""

from __future__ import annotations

from . import bp_web


@bp_web.get("/")
def home() -> tuple[str, int] | str:
    """Página principal con mensaje de bienvenida."""

    return "Hola desde Elyra + Render 🚀"


@bp_web.get("/health")
def health() -> tuple[str, int]:
    """Ruta de salud para chequeos automatizados."""

    return "ok", 200
