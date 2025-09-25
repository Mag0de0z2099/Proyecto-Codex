"""Ensure approval fields exist on users table."""

from __future__ import annotations

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "20250924_add_approval_fields"
down_revision = "20251008_auth_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}

    added_columns: list[str] = []
    with op.batch_alter_table("users", schema=None) as batch:
        if "is_active" not in columns:
            batch.add_column(
                sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
            )
            added_columns.append("is_active")
        if "is_approved" not in columns:
            batch.add_column(
                sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false())
            )
            added_columns.append("is_approved")
        if "approved_at" not in columns:
            batch.add_column(sa.Column("approved_at", sa.DateTime(), nullable=True))
            added_columns.append("approved_at")

    true_literal = "TRUE" if bind.dialect.name == "postgresql" else "1"
    false_literal = "FALSE" if bind.dialect.name == "postgresql" else "0"

    if "is_active" in added_columns:
        op.execute(sa.text(f"UPDATE users SET is_active = {true_literal} WHERE is_active IS NULL"))
        with op.batch_alter_table("users", schema=None) as batch:
            batch.alter_column("is_active", server_default=None)

    if "is_approved" in added_columns:
        op.execute(
            sa.text(
                f"UPDATE users SET is_approved = {false_literal} WHERE is_approved IS NULL"
            )
        )
        with op.batch_alter_table("users", schema=None) as batch:
            batch.alter_column("is_approved", server_default=None)

    if "approved_at" in added_columns:
        op.execute(
            sa.text(
                "UPDATE users SET approved_at = :timestamp WHERE approved_at IS NULL AND is_approved = :true"
            ),
            {"timestamp": datetime.now(timezone.utc), "true": True},
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch:
        if _has_column("users", "approved_at"):
            batch.drop_column("approved_at")
        if _has_column("users", "is_approved"):
            batch.drop_column("is_approved")
        if _has_column("users", "is_active"):
            batch.drop_column("is_active")


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))

