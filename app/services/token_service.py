from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models.refresh_token import RefreshToken

REFRESH_TTL_DAYS = 7


def _expiry() -> datetime:
    return datetime.utcnow() + timedelta(days=REFRESH_TTL_DAYS)


def create_refresh_record(user_id: int, jti: str) -> RefreshToken:
    row = RefreshToken(user_id=user_id, jti=jti, expires_at=_expiry(), revoked=False)
    db.session.add(row)
    db.session.commit()
    return row


def revoke_jti(jti: str) -> int:
    updated = (
        RefreshToken.query.filter_by(jti=jti, revoked=False)
        .update({"revoked": True}, synchronize_session=False)
    )
    db.session.commit()
    return updated


def revoke_all_for_user(user_id: int) -> int:
    updated = (
        RefreshToken.query.filter_by(user_id=user_id, revoked=False)
        .update({"revoked": True}, synchronize_session=False)
    )
    db.session.commit()
    return updated


def is_active(jti: str, user_id: int) -> bool:
    row = RefreshToken.query.filter_by(jti=jti, user_id=user_id).first()
    if row is None:
        return False
    if row.revoked:
        return False
    if row.expires_at <= datetime.utcnow():
        return False
    return True
