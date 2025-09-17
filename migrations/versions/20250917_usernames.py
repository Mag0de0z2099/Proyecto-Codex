"""add username (unique, not null) and make email nullable"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20250917_usernames"
down_revision = "20250916_add_force_change_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, email FROM users ORDER BY id")).fetchall()
    taken: set[str] = set()
    for rid, email in rows:
        base = None
        if email:
            base = email.split("@", 1)[0].strip() or None
        if not base:
            base = f"user{rid}"
        candidate = base[:64]
        original = candidate or f"user{rid}"
        candidate = original
        counter = 1
        while not candidate or candidate in taken:
            suffix = str(counter)
            trimmed = original[: max(1, 64 - len(suffix))]
            candidate = f"{trimmed}{suffix}"
            counter += 1
        taken.add(candidate)
        conn.execute(
            sa.text("UPDATE users SET username=:u WHERE id=:id"),
            {"u": candidate, "id": rid},
        )

    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_unique_constraint("uq_users_username", "users", ["username"])

    op.drop_index("ix_users_email", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "email",
            existing_type=sa.String(length=254),
            nullable=True,
        )
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "email",
            existing_type=sa.String(length=254),
            nullable=False,
        )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
