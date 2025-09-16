"""Punto de entrada para ejecutar la aplicación Flask."""

from __future__ import annotations

from flask import Flask

from . import create_app

app: Flask = create_app()


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    app.run(debug=True)
