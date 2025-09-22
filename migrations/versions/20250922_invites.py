"""create invites table"""

from alembic import op
import sqlalchemy as sa


revision = "20250922_invites"
down_revision = "20251007_assets_and_folders"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("max_uses", sa.Integer, nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_invites_token", "invites", ["token"], unique=True)
    op.create_index("ix_invites_email", "invites", ["email"])


def downgrade():
    op.drop_index("ix_invites_email", table_name="invites")
    op.drop_index("ix_invites_token", table_name="invites")
    op.drop_table("invites")
