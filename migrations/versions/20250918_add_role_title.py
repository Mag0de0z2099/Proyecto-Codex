"""add role and title to users (sqlite-safe)"""
from alembic import op
import sqlalchemy as sa

revision = "20250918_add_role_title"
down_revision = "20250917_create_folders"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch:
        batch.add_column(
            sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer")
        )
        batch.add_column(sa.Column("title", sa.String(length=80), nullable=True))
        batch.create_index("ix_users_role", ["role"], unique=False)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_index("ix_users_role")
        batch.drop_column("title")
        batch.drop_column("role")
