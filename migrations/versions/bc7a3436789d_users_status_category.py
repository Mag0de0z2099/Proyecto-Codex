"""users status & category"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "bc7a3436789d"
down_revision = "20251007_assets_and_folders"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "users",
        sa.Column("category", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    if dialect != "sqlite":
        op.create_check_constraint(
            "ck_users_status",
            "users",
            "status IN ('pending','approved','rejected')",
        )
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_category", "users", ["category"])

    now_sql = "CURRENT_TIMESTAMP" if dialect == "sqlite" else "NOW()"
    statement = text(
        "UPDATE users\n"
        f"   SET status='approved', approved_at={now_sql}, is_active=TRUE\n"
        " WHERE is_admin = TRUE OR role='admin'"
    )
    conn.execute(statement)


def downgrade():
    op.drop_index("ix_users_category", table_name="users")
    op.drop_index("ix_users_status", table_name="users")
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        op.drop_constraint("ck_users_status", "users", type_="check")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "category")
    op.drop_column("users", "status")
