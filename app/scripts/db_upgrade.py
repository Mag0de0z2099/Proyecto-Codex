from __future__ import annotations

from flask_migrate import upgrade

from app import create_app


def main() -> None:
    app = create_app()
    with app.app_context():
        upgrade()


if __name__ == "__main__":
    main()
