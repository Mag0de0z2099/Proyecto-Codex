"""merge heads for checklist branches"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "rev_20251013_merge_heads"
down_revision = ("rev_20250926_partes_cl_fk", "rev_20251013_pdiarias")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
