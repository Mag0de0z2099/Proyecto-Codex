from __future__ import annotations

from datetime import datetime, timedelta

PASSWORD_MIN = 12
LOCK_MAX_ATTEMPTS = 5
LOCK_COOLDOWN_MIN = 15
SESSION_IDLE_MIN = 20


def is_locked(user, now: datetime | None = None) -> bool:
    now = now or datetime.utcnow()
    return bool(getattr(user, "lock_until", None) and user.lock_until > now)


def register_fail(user, now: datetime | None = None) -> None:
    from app import db

    now = now or datetime.utcnow()
    current = getattr(user, "failed_logins", 0) or 0
    user.failed_logins = current + 1
    if user.failed_logins >= LOCK_MAX_ATTEMPTS:
        user.lock_until = now + timedelta(minutes=LOCK_COOLDOWN_MIN)
    db.session.commit()


def reset_fail_counter(user) -> None:
    from app import db

    user.failed_logins = 0
    user.lock_until = None
    db.session.commit()
