"""Punto de entrada WSGI para Gunicorn y servidores similares."""

from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run()
