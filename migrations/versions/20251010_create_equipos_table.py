"""create equipos table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251010_create_equipos_table"
down_revision = "rev_20250924_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("tipo", sa.String(length=64), nullable=False),
        sa.Column("marca", sa.String(length=64), nullable=True),
        sa.Column("modelo", sa.String(length=64), nullable=True),
        sa.Column("serie", sa.String(length=128), nullable=True),
        sa.Column("placas", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True, server_default="activo"),
        sa.Column("ubicacion", sa.String(length=128), nullable=True),
        sa.Column(
            "horas_uso",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        sa.Column("fecha_alta", sa.Date(), nullable=True, server_default=sa.func.current_date()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("codigo", name="uq_equipos_codigo"),
    )
    op.create_index("ix_equipos_codigo", "equipos", ["codigo"])


def downgrade() -> None:
    op.drop_index("ix_equipos_codigo", table_name="equipos")
    op.drop_table("equipos")
