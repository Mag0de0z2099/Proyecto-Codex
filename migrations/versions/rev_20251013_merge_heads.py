"""merge heads for checklist branches"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "rev_20251013_merge_heads"
down_revision = ("rev_20250926_partes_cl_fk", "20251013_create_partes_diarias_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
