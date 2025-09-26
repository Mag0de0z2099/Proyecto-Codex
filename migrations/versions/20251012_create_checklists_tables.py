"""create checklists core tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251012_create_checklists_tables"
down_revision = "20251011_create_operadores_table"
branch_labels = None
depends_on = None

answer_enum = sa.Enum("OK", "FAIL", "NA", name="answerenum")


def upgrade() -> None:
    bind = op.get_bind()
    answer_enum.create(bind, checkfirst=True)

    op.create_table(
        "cl_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("applies_to", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "cl_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("cl_templates.id"), nullable=False),
        sa.Column("section", sa.String(length=64), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("critical", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "checklists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("cl_templates.id"), nullable=False),
        sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipos.id"), nullable=False),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("operadores.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=True, server_default=sa.func.current_date()),
        sa.Column("shift", sa.String(length=16), nullable=True),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column("weather", sa.String(length=64), nullable=True),
        sa.Column("hours_start", sa.Float(), nullable=True),
        sa.Column("hours_end", sa.Float(), nullable=True),
        sa.Column("overall_status", sa.String(length=16), nullable=False, server_default="APTO"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "cl_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checklist_id", sa.Integer(), sa.ForeignKey("checklists.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("cl_items.id"), nullable=False),
        sa.Column("result", answer_enum, nullable=False, server_default="OK"),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("photo_path", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("cl_answers")
    op.drop_table("checklists")
    op.drop_table("cl_items")
    op.drop_table("cl_templates")
    bind = op.get_bind()
    answer_enum.drop(bind, checkfirst=True)
