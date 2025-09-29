"""create operadores table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251011_create_operadores_table"
down_revision = "20251010_create_equipos_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operadores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("doc_id", sa.String(length=80), nullable=True),
        sa.Column("licencia_vence", sa.Date(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column(
            "estatus",
            sa.String(length=32),
            nullable=True,
            server_default="activo",
        ),
    )
    op.create_index("ix_operadores_nombre", "operadores", ["nombre"])


def downgrade() -> None:
    op.drop_index("ix_operadores_nombre", table_name="operadores")
    op.drop_table("operadores")
