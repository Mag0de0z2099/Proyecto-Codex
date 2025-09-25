"""add approval flags to users"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "20251008_auth_flags"
down_revision = "bc7a3436789d"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    missing_email_rows = conn.execute(text("SELECT id FROM users WHERE email IS NULL")).fetchall()
    for row in missing_email_rows:
        placeholder = f"user{row.id}@example.invalid"
        conn.execute(
            text("UPDATE users SET email = :email WHERE id = :id"),
            {"email": placeholder, "id": row.id},
        )

    with op.batch_alter_table("users", schema=None) as batch:
        batch.alter_column(
            "email",
            existing_type=sa.String(length=254),
            nullable=False,
        )
        batch.add_column(
            sa.Column(
                "is_approved",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )

    approved_condition = text(
        "UPDATE users\n"
        "   SET is_approved = 1\n"
        " WHERE lower(COALESCE(status, '')) = 'approved' OR is_admin = 1"
    )
    if dialect == "postgresql":
        approved_condition = text(
            "UPDATE users\n"
            "   SET is_approved = TRUE\n"
            " WHERE lower(COALESCE(status, '')) = 'approved' OR is_admin = TRUE"
        )

    conn.execute(approved_condition)

    timestamp_sql = "CURRENT_TIMESTAMP"
    if dialect == "postgresql":
        timestamp_sql = "TIMEZONE('utc', NOW())"

    conn.execute(
        text(
            "UPDATE users\n"
            f"   SET approved_at = {timestamp_sql}\n"
            " WHERE is_approved = :true AND approved_at IS NULL"
        ),
        {"true": True if dialect == "postgresql" else 1},
    )

    if dialect != "sqlite":
        op.alter_column("users", "is_approved", server_default=None)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_column("is_approved")
        batch.alter_column(
            "email",
            existing_type=sa.String(length=254),
            nullable=True,
        )
