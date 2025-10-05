"""Security policy helpers for lockouts and password hygiene."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.db import db

PASSWORD_MIN = 12
LOCK_MAX_ATTEMPTS = 5
LOCK_COOLDOWN_MIN = 15
SESSION_IDLE_MIN = 20


def is_locked(user, now: datetime | None = None) -> bool:
    """Return True if the user is currently locked out."""

    now = now or datetime.utcnow()
    lock_until = getattr(user, "lock_until", None)
    return bool(lock_until and lock_until > now)


def register_fail(user, now: datetime | None = None) -> None:
    """Increment failed login counter and lock the account if needed."""

    now = now or datetime.utcnow()
    failed = getattr(user, "failed_logins", 0) or 0
    user.failed_logins = failed + 1
    if user.failed_logins >= LOCK_MAX_ATTEMPTS:
        user.lock_until = now + timedelta(minutes=LOCK_COOLDOWN_MIN)
    db.session.commit()


def reset_fail_counter(user) -> None:
    """Reset failed login counters after a successful authentication."""

    user.failed_logins = 0
    user.lock_until = None
    db.session.commit()


__all__ = [
    "PASSWORD_MIN",
    "LOCK_MAX_ATTEMPTS",
    "LOCK_COOLDOWN_MIN",
    "SESSION_IDLE_MIN",
    "is_locked",
    "register_fail",
    "reset_fail_counter",
]
