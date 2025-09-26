from app import db
from app.models import User


def test_user_password_hashing(app):
    user = User(email="a@a.com", username="user")
    user.set_password("secret")
    db.session.add(user)
    db.session.commit()

    assert user.check_password("secret") is True
    assert user.check_password("nope") is False
