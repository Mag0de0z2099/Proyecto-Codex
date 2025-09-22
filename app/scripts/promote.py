"""
Promueve un usuario a admin:  python -m app.scripts.promote <usuario>
"""
from __future__ import annotations

import sys

from app import create_app
from app import db
from app.models import User


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python -m app.scripts.promote <usuario>")
        return
    username = sys.argv[1]
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Usuario {username} no existe.")
            return
        user.role = "admin"
        user.is_active = True
        db.session.commit()
        print(f"OK: {username} ahora es admin.")


if __name__ == "__main__":
    main()
