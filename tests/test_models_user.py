from app import db
from app.models import User


def test_password_hashing(app):
    user = User(email="x@y.com", username="userx")
    user.set_password("s3cr3t")
    assert user.check_password("s3cr3t") is True
    assert user.check_password("nope") is False


def test_email_normalization(app):
    user = User(email=" MAYUS@MAIL.COM ")
    if hasattr(User, "username"):
        user.username = "  ADMIN  "
    user.set_password("secret")
    db.session.add(user)
    db.session.commit()

    assert user.email == "mayus@mail.com" or user.email.strip().lower() == user.email
    if hasattr(User, "username"):
        assert user.username == user.username.strip().lower()
