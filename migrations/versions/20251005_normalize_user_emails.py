"""normalize stored user emails"""
from alembic import op
import sqlalchemy as sa

revision = "20251005_normalize_user_emails"
down_revision = "20250918_add_role_title"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        sa.text("UPDATE users SET email = lower(trim(email)) WHERE email IS NOT NULL")
    )


def downgrade():
    # No se puede restaurar la capitalización original de forma confiable.
    pass
