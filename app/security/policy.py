import re
from datetime import datetime, timedelta

LOCK_MAX_ATTEMPTS = 5
LOCK_COOLDOWN_MIN = 15

_pwd_re = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,}$")

def is_locked(user, now=None):
    now = now or datetime.utcnow()
    return bool(getattr(user, "lock_until", None) and user.lock_until > now)

def register_fail(user, db, now=None):
    now = now or datetime.utcnow()
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= LOCK_MAX_ATTEMPTS:
        user.lock_until = now + timedelta(minutes=LOCK_COOLDOWN_MIN)
    db.session.commit()

def reset_fail_counter(user, db):
    user.failed_logins = 0
    user.lock_until = None
    db.session.commit()

def password_ok(pwd: str) -> bool:
    """≥12, al menos 1 minúscula, 1 mayúscula, 1 dígito"""
    return bool(_pwd_re.match(pwd or ""))
