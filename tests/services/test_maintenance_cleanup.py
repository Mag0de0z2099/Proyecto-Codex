from __future__ import annotations

from datetime import datetime, timedelta

from app.extensions import db
from app.models.refresh_token import RefreshToken
from app.services.maintenance_service import cleanup_expired_refresh_tokens


def _make_refresh(
    *,
    user_id: int = 1,
    created_days_offset: int = -10,
    expires_days_offset: int | None = None,
    revoked: bool = False,
) -> RefreshToken:
    now = datetime.utcnow()
    exp_offset = expires_days_offset if expires_days_offset is not None else created_days_offset
    row = RefreshToken(
        user_id=user_id,
        jti=f"jti_{user_id}_{abs(created_days_offset)}_{int(revoked)}",
        created_at=now + timedelta(days=created_days_offset),
        expires_at=now + timedelta(days=exp_offset),
        revoked=revoked,
    )
    db.session.add(row)
    db.session.commit()
    return row


def test_cleanup_removes_expired_tokens(client, app_ctx):
    _make_refresh(user_id=1, created_days_offset=-8, revoked=False)
    _make_refresh(user_id=2, created_days_offset=-3, revoked=True)
    _make_refresh(user_id=3, created_days_offset=2, revoked=False)

    result = cleanup_expired_refresh_tokens(grace_days=0)

    assert result["removed_expired"] == 2
    assert RefreshToken.query.count() == 1


def test_cleanup_respects_grace_and_revoked(client, app_ctx):
    expired_recent = _make_refresh(
        user_id=10,
        created_days_offset=-1,
        expires_days_offset=-1,
        revoked=False,
    )
    revoked_old = _make_refresh(
        user_id=11,
        created_days_offset=-30,
        expires_days_offset=5,
        revoked=True,
    )
    active = _make_refresh(user_id=12, created_days_offset=0, expires_days_offset=10)

    expired_recent_id = expired_recent.id
    revoked_old_id = revoked_old.id
    active_id = active.id

    result = cleanup_expired_refresh_tokens(grace_days=2)

    assert result["removed_expired"] == 0
    assert result["removed_revoked"] == 1

    remaining_ids = {row.id for row in RefreshToken.query.all()}
    assert expired_recent_id in remaining_ids  # within grace window
    assert active_id in remaining_ids
    assert revoked_old_id not in remaining_ids
