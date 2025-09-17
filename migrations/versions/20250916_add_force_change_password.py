"""add force_change_password to users"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250916_add_force_change_password"
down_revision = "20240201_create_users"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("force_change_password", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("users", "force_change_password", server_default=None)


def downgrade():
    op.drop_column("users", "force_change_password")
