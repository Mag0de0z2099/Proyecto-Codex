"""Punto de entrada principal para la aplicación Flask."""

from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """Crea y configura una instancia de la aplicación Flask."""
    app = Flask(__name__)

    @app.get("/")
    def home() -> str:
        """Devuelve un texto de bienvenida simple."""
        return "Elyra + Render"

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - ejecución manual
    app.run(debug=True)
