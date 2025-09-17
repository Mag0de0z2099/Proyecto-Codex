"""add force_change_password to users (sqlite-safe)"""
from alembic import op
import sqlalchemy as sa

# OJO: deja estos IDs como los tienes en tu repo
revision = "20250916_add_force_change_password"
down_revision = "20240201_create_users"
branch_labels = None
depends_on = None


def upgrade():
    # Añadimos la columna con default False para que SQLite permita NOT NULL
    op.add_column(
        "users",
        sa.Column(
            "force_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Si NO es SQLite, puedes quitar el default (opcional)
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column("users", "force_change_password", server_default=None)


def downgrade():
    op.drop_column("users", "force_change_password")
