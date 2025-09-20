from __future__ import annotations

from app.db import db


class Folder(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    logical_path = db.Column(db.String(512), nullable=False)
    fs_path = db.Column(db.String(1024), nullable=False)
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
        "Project",
        backref=db.backref("folders", cascade="all, delete-orphan", lazy=True),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "project_id", "logical_path", name="uq_folder_project_path"
        ),
        db.Index("ix_folders_project_id", "project_id"),
    )
