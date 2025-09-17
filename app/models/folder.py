from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db


class Folder(db.Model):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("folders.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_root: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    parent: Mapped["Folder"] = relationship(
        "Folder", remote_side=[id], backref="children", cascade="all,delete"
    )

    __table_args__ = (UniqueConstraint("parent_id", "slug", name="uq_folders_parent_slug"),)

    def __repr__(self) -> str:
        return f"<Folder {self.id}:{self.name} parent={self.parent_id}>"
