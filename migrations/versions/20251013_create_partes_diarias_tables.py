"""create partes diarias tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251013_create_partes_diarias_tables"
down_revision = "rev_20251012_checklists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partes_diarias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("equipo_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
        sa.Column("operador_id", sa.Integer(), sa.ForeignKey("operadores.id"), nullable=True),
        sa.Column("turno", sa.String(length=16), nullable=False, server_default="matutino"),
        sa.Column("ubicacion", sa.String(length=128), nullable=True),
        sa.Column("clima", sa.String(length=64), nullable=True),
        sa.Column("horas_inicio", sa.Float(), nullable=True),
        sa.Column("horas_fin", sa.Float(), nullable=True),
        sa.Column("horas_trabajadas", sa.Float(), nullable=True),
        sa.Column("combustible_l", sa.Float(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )
    op.create_index("ix_partes_diarias_fecha", "partes_diarias", ["fecha"])
    op.create_index("ix_partes_diarias_equipo_id", "partes_diarias", ["equipo_id"])
    op.create_index("ix_partes_diarias_operador_id", "partes_diarias", ["operador_id"])

    op.create_table(
        "actividades_diarias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "parte_id",
            sa.Integer(),
            sa.ForeignKey("partes_diarias.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.Column("cantidad", sa.Float(), nullable=True),
        sa.Column("unidad", sa.String(length=32), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_actividades_diarias_parte_id", "actividades_diarias", ["parte_id"])


def downgrade() -> None:
    op.drop_index("ix_actividades_diarias_parte_id", table_name="actividades_diarias")
    op.drop_table("actividades_diarias")
    op.drop_index("ix_partes_diarias_operador_id", table_name="partes_diarias")
    op.drop_index("ix_partes_diarias_equipo_id", table_name="partes_diarias")
    op.drop_index("ix_partes_diarias_fecha", table_name="partes_diarias")
    op.drop_table("partes_diarias")
