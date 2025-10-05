"""Registro perezoso de comandos CLI."""

from __future__ import annotations


def register_commands(app):
    """Registrar los comandos CLI principales evitando ciclos tempranos."""

    from .cli import register_cli
    from .cli_sync import register_sync_cli

    register_cli(app)
    register_sync_cli(app)
