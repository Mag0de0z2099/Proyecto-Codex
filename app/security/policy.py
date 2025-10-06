"""Security policy helpers for lockouts and password hygiene."""

from __future__ import annotations

from datetime import datetime, timedelta

LOCK_MAX_ATTEMPTS = 5
LOCK_COOLDOWN_MIN = 15
PASSWORD_MIN = 12
SESSION_IDLE_MIN = 20


def is_locked(user, now: datetime | None = None) -> bool:
    """Return True if the user is currently locked out."""

    now = now or datetime.utcnow()
    return bool(getattr(user, "lock_until", None) and user.lock_until > now)


def register_fail(user, db, now: datetime | None = None) -> None:
    """Increment failed login counter and lock the account if needed."""

    now = now or datetime.utcnow()
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= LOCK_MAX_ATTEMPTS:
        user.lock_until = now + timedelta(minutes=LOCK_COOLDOWN_MIN)
    db.session.commit()


def reset_fail_counter(user, db) -> None:
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
