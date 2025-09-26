from app.models import User


def test_seed_admin_crea_y_actualiza(runner, app):
    res = runner.invoke(
        args=["seed-admin", "--email", "admin@admin.com", "--password", "admin123"]
    )
    assert res.exit_code == 0

    with app.app_context():
        user = User.query.filter_by(email="admin@admin.com").first()
        assert user is not None
        assert user.check_password("admin123")
        for flag in ["is_active", "active", "approved", "is_approved", "email_verified"]:
            if hasattr(user, flag):
                assert getattr(user, flag) in (True, 1, "approved")

    res2 = runner.invoke(
        args=["seed-admin", "--email", "admin@admin.com", "--password", "newpass"]
    )
    assert res2.exit_code == 0

    with app.app_context():
        updated_user = User.query.filter_by(email="admin@admin.com").first()
        assert updated_user is not None
        assert updated_user.check_password("newpass")


def test_show_user_imprime_campos(runner, app):
    runner.invoke(
        args=["seed-admin", "--email", "admin@admin.com", "--password", "x"]
    )

    res = runner.invoke(args=["show-user", "--id", "admin@admin.com"])
    assert res.exit_code == 0
    assert "admin@admin.com" in res.output
