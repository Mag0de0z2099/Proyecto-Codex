"""Maintenance helpers for background/cron jobs."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models.refresh_token import RefreshToken


def cleanup_expired_refresh_tokens(grace_days: int = 0) -> dict[str, int]:
    """Remove expired refresh tokens (and old revoked ones).

    Args:
        grace_days: Number of days to keep expired records for debugging/audit.

    Returns:
        A dictionary with the number of removed records.
    """

    now = datetime.utcnow()
    cutoff = now - timedelta(days=max(grace_days, 0))

    try:
        expired_q = RefreshToken.query.filter(RefreshToken.expires_at <= cutoff)
        removed_expired = expired_q.delete(synchronize_session=False)

        revoked_q = RefreshToken.query.filter(
            RefreshToken.revoked.is_(True), RefreshToken.created_at <= cutoff
        )
        removed_revoked = revoked_q.delete(synchronize_session=False)

        db.session.commit()
        return {
            "removed_expired": int(removed_expired or 0),
            "removed_revoked": int(removed_revoked or 0),
        }
    except OperationalError:
        db.session.rollback()
        return {"removed_expired": 0, "removed_revoked": 0}
