"""Utility helpers for paginating SQLAlchemy queries in Flask views."""

from __future__ import annotations

from dataclasses import dataclass

from app.extensions import db


@dataclass
class SimplePagination:
    """Lightweight pagination object mimicking Flask-SQLAlchemy's API."""

    page: int
    per_page: int
    total: int
    pages: int

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self) -> int | None:
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self) -> int | None:
        return self.page + 1 if self.has_next else None


def paginate(query, page: int, per_page: int):
    """Return items and a pagination object for the given query.

    Falls back to manual pagination when Flask-SQLAlchemy's helper is not
    available (e.g., during unit tests or when using a plain SQLAlchemy query).
    """

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
        return items, pagination
    except Exception:
        total = query.count()
        pages = max((total + per_page - 1) // per_page, 1)
        if page > pages:
            page = pages
        offset = max((page - 1) * per_page, 0)
        items = list(query.offset(offset).limit(per_page).all())
        pagination = SimplePagination(
            page=page,
            per_page=per_page,
            total=total,
            pages=pages,
        )
        return items, pagination
