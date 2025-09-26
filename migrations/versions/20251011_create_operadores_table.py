"""create operadores table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "rev_20251011_operadores"
down_revision = "20251010_create_equipos_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operadores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("identificacion", sa.String(length=64), nullable=True),
        sa.Column("licencia", sa.String(length=64), nullable=True),
        sa.Column("puesto", sa.String(length=64), nullable=True),
        sa.Column("telefono", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=True,
            server_default="activo",
        ),
        sa.Column(
            "fecha_alta",
            sa.Date(),
            nullable=True,
            server_default=sa.func.current_date(),
        ),
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
        sa.UniqueConstraint("identificacion", name="uq_operadores_identificacion"),
    )
    op.create_index("ix_operadores_nombre", "operadores", ["nombre"])


def downgrade() -> None:
    op.drop_index("ix_operadores_nombre", table_name="operadores")
    op.drop_table("operadores")
