"""create folders table"""
from alembic import op
import sqlalchemy as sa


revision = "20250917_create_folders"
down_revision = "20250917_usernames"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_root", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint("uq_folders_parent_slug", "folders", ["parent_id", "slug"])


def downgrade():
    op.drop_constraint("uq_folders_parent_slug", "folders", type_="unique")
    op.drop_table("folders")
