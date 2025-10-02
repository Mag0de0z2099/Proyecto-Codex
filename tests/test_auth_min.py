from __future__ import annotations


def test_admin_seed_cli(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["users:seed-admin", "--email", "admin@admin.com", "--password", "admin123"],
    )
    assert result.exit_code == 0


def test_protected_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
