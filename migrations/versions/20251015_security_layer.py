"""Add lockout counters and TOTP secret to users."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251015_security_layer"
down_revision = "20251014_alembic_version_64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_logins", sa.Integer(), server_default="0"))
    op.add_column("users", sa.Column("lock_until", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("totp_secret", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "totp_secret")
    op.drop_column("users", "lock_until")
    op.drop_column("users", "failed_logins")
