"""Initial tables for core Codex models."""

from alembic import op
import sqlalchemy as sa


revision = "d736c9cafb61"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("client", sa.String(length=120), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'activo'"),
        ),
        sa.Column(
            "progress",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "budget",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "spent",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("name", name="uq_projects_name"),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=60), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'borrador'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "bitacoras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "date",
            sa.Date(),
            nullable=False,
            server_default=sa.func.current_date(),
        ),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "metrics_daily",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kpi_name", sa.String(length=80), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "value",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "checklist_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("name", name="uq_checklist_templates_name"),
    )

    op.create_table(
        "checklist_template_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "template_id",
            sa.Integer(),
            sa.ForeignKey("checklist_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column(
            "order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_table(
        "daily_checklists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_by", sa.String(length=80), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'en_progreso'"),
        ),
    )

    op.create_table(
        "daily_checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "checklist_id",
            sa.Integer(),
            sa.ForeignKey("daily_checklists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column(
            "done",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )


def downgrade():
    op.drop_table("todos")
    op.drop_table("daily_checklist_items")
    op.drop_table("daily_checklists")
    op.drop_table("checklist_template_items")
    op.drop_table("checklist_templates")
    op.drop_table("metrics_daily")
    op.drop_table("bitacoras")
    op.drop_table("reports")
    op.drop_table("projects")
