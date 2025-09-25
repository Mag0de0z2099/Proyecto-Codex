from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.models import User
from app.utils.strings import normalize_email


def verify_credentials(email: str, password: str):
    if not email or not password:
        return None

    user = User.query.filter_by(email=email).first()
    if not user:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user


def ensure_admin_user(
    *, email: str, password: str, username: str | None = None
) -> User:
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("invalid email")

    resolved_username = username or normalized_email.split("@", 1)[0]

    user = User.query.filter_by(email=normalized_email).one_or_none()
    if user is None:
        user = User(email=normalized_email, username=resolved_username)
        db.session.add(user)
    else:
        if hasattr(user, "username") and username:
            user.username = resolved_username

    if hasattr(user, "set_password"):
        user.set_password(password)
    else:
        user.password_hash = generate_password_hash(password)

    if hasattr(user, "role"):
        user.role = "admin"
    if hasattr(user, "is_admin"):
        user.is_admin = True
    if hasattr(user, "is_active"):
        user.is_active = True
    if hasattr(user, "status"):
        user.status = "approved"
    if hasattr(user, "is_approved"):
        user.is_approved = True
    if hasattr(user, "approved_at") and user.approved_at is None:
        user.approved_at = datetime.now(timezone.utc)
    if hasattr(user, "force_change_password"):
        user.force_change_password = False

    db.session.commit()
    return user

