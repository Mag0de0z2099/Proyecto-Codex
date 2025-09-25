"""ensure role column exists on users"""

from alembic import op
import sqlalchemy as sa

revision = "20250924_add_role_to_user"
down_revision = "20250924_add_approval_fields"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in columns


def upgrade() -> None:
    if not _has_column("users", "role"):
        with op.batch_alter_table("users", schema=None) as batch:
            batch.add_column(
                sa.Column("role", sa.String(length=32), nullable=False, server_default="user")
            )
        with op.batch_alter_table("users", schema=None) as batch:
            batch.alter_column("role", server_default=None)


def downgrade() -> None:
    if _has_column("users", "role"):
        with op.batch_alter_table("users", schema=None) as batch:
            batch.drop_column("role")
