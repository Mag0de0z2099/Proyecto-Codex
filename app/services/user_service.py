from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import User


def list_users(status: str | None = None) -> list[User]:
    try:
        q = User.query
        if status == "pending":
            q = q.filter(User.is_approved.is_(False))
        elif status == "approved":
            q = q.filter(User.is_approved.is_(True))
        return q.order_by(User.id.asc()).all()
    except SQLAlchemyError:
        db.session.rollback()
        return []


def approve_user(user_id: int) -> User | None:
    user = User.query.get(user_id)
    if not user:
        return None
    if hasattr(user, "approve"):
        try:
            user.approve()
        except Exception:
            user.is_approved = True
            if hasattr(user, "status"):
                try:
                    user.status = "approved"
                except Exception:
                    pass
            user.approved_at = datetime.now(timezone.utc)
    else:
        user.is_approved = True
        if hasattr(user, "status"):
            try:
                user.status = "approved"
            except Exception:
                pass
        user.approved_at = datetime.now(timezone.utc)
    db.session.commit()
    return user
