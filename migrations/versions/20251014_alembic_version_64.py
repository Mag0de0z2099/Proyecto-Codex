"""widen alembic version_num column"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251014_alembic_version_64"
down_revision = "rev_20251013_merge_heads"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("alembic_version") as batch:
        batch.alter_column("version_num", type_=sa.String(64))


def downgrade():
    with op.batch_alter_table("alembic_version") as batch:
        batch.alter_column("version_num", type_=sa.String(32))
