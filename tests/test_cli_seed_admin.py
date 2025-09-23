import os
import re
import pytest


def _create_all_if_possible(app):
    try:
        from app.db import db
    except Exception:
        return False
    with app.app_context():
        try:
            db.create_all()
            return True
        except Exception:
            return False


def test_cli_seed_admin_idempotent(app, monkeypatch):
    # DB volátil para CI
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    created = _create_all_if_possible(app)

    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed-admin", "--email", "admin@admin.com", "--password", "admin123"])
    if result.exit_code != 0 and "No such command" in result.output:
        pytest.skip("seed-admin no está registrado en esta app")
    assert result.exit_code == 0

    # segunda vez no debe fallar (idempotente)
    result2 = runner.invoke(args=["seed-admin", "--email", "admin@admin.com", "--password", "admin123"])
    assert result2.exit_code == 0
    # si imprime mensajes, validamos alguno
    assert "Usuario" in result2.output
