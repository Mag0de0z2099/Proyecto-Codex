from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa

from app.extensions import db
from app.models import User


def list_users(
    status: str | None = None,
    search: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> tuple[list[User], dict[str, int]]:
    """Return users filtered by status/search with optional pagination."""

    query = User.query

    if status == "pending":
        query = query.filter(User.is_approved.is_(False))
    elif status == "approved":
        query = query.filter(User.is_approved.is_(True))

    if search:
        term = f"%{search.strip().lower()}%"
        query = query.filter(sa.func.lower(User.email).like(term))

    query = query.order_by(User.id.asc())

    if page is not None and per_page is not None:
        page = max(int(page or 1), 1)
        per_page = max(int(per_page or 1), 1)
        try:
            pagination = db.paginate(
                query,
                page=page,
                per_page=per_page,
                error_out=False,
            )
            items = list(pagination.items)
            meta = {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "total": pagination.total,
            }
            return items, meta
        except Exception:
            total = query.count()
            pages = (total + per_page - 1) // per_page if total else 0
            if pages and page > pages:
                page = pages
            elif not pages:
                page = 1
            offset = max((page - 1) * per_page, 0)
            items = query.offset(offset).limit(per_page).all()
            meta = {
                "page": page,
                "per_page": per_page,
                "pages": pages or 1,
                "total": total,
            }
            return list(items), meta

    items = query.all()
    total = len(items)
    meta = {"page": 1, "per_page": total, "pages": 1, "total": total}
    return list(items), meta


def approve_user(user_id: int) -> User | None:
    """Approve a user by ID."""

    user = db.session.get(User, user_id)
    if user is None:
        return None

    if hasattr(user, "approve"):
        user.approve()
    else:
        user.is_approved = True
        if hasattr(user, "status"):
            try:
                user.status = "approved"
            except Exception:
                pass
        if hasattr(user, "approved_at") and getattr(user, "approved_at", None) is None:
            user.approved_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return user
