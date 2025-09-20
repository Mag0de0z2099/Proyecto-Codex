from __future__ import annotations

from app.db import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    folder_id = db.Column(
        db.Integer, db.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True
    )
    filename = db.Column(db.String(512), nullable=False)
    relative_path = db.Column(db.String(1024), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, index=True)
    mime_type = db.Column(db.String(128))
    version = db.Column(
        db.Integer, nullable=False, default=1, server_default=db.text("1")
    )
    metadata_json = db.Column("metadata", db.JSON)
    created_at = db.Column(
        db.DateTime, default=db.func.now(), server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        server_default=db.func.current_timestamp(),
    )

    project = db.relationship(
        "Project", backref=db.backref("assets", cascade="all, delete-orphan")
    )
    folder = db.relationship(
        "Folder", backref=db.backref("assets", cascade="all"), lazy=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "project_id", "folder_id", "relative_path", name="uq_asset_scope_path"
        ),
        db.Index("ix_assets_project_id", "project_id"),
        db.Index("ix_assets_folder_id", "folder_id"),
    )

