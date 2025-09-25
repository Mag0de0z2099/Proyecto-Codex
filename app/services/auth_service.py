"""Authentication related services."""

from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.db import db
from app.models import User
from app.utils.strings import normalize_email


def verify_credentials(email: str, password: str) -> User | None:
    """Return the user when the provided credentials are valid."""
    normalized_email = normalize_email(email)
    if not normalized_email or not password:
        return None

    user = User.query.filter_by(email=normalized_email).first()
    if user is None:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user


def ensure_admin_user(email: str, password: str, username: str | None = None) -> User:
    """Create or update the administrator account."""
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("Email is required")

    user = User.query.filter_by(email=normalized_email).first()
    if user is None:
        base_username = (username or normalized_email.split("@", 1)[0] or "admin").strip() or "admin"
        candidate = base_username
        suffix = 1
        while User.query.filter_by(username=candidate).first():
            candidate = f"{base_username}{suffix}"
            suffix += 1

        user = User(
            username=candidate,
            email=normalized_email,
            role="admin",
            is_admin=True,
        )
        db.session.add(user)

    user.password_hash = generate_password_hash(password)
    user.is_active = True
    user.is_approved = True
    user.approved_at = datetime.now(timezone.utc)
    user.status = "approved"
    user.role = "admin"
    user.is_admin = True
    user.force_change_password = False

    db.session.commit()
    return user
