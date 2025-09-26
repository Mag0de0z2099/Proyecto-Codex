"""Add checklist foreign key to partes diarias"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "rev_20250926_partes_cl_fk"
down_revision = "20251013_create_partes_diarias_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("partes_diarias") as b:
        b.add_column(sa.Column("checklist_id", sa.Integer(), nullable=True))
        b.create_index("ix_partes_diarias_checklist_id", ["checklist_id"])
        b.create_foreign_key(
            "fk_partes_checklist", "checklists", ["checklist_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("partes_diarias") as b:
        b.drop_constraint("fk_partes_checklist", type_="foreignkey")
        b.drop_index("ix_partes_diarias_checklist_id")
        b.drop_column("checklist_id")
