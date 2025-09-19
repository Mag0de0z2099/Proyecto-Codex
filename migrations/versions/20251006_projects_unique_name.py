"""add unique constraint to projects.name"""

from alembic import op


revision = "20251006_projects_unique_name"
down_revision = "20251005_normalize_user_emails"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_unique_constraint("uq_projects_name", "projects", ["name"])
    except Exception:
        pass


def downgrade():
    try:
        op.drop_constraint("uq_projects_name", "projects", type_="unique")
    except Exception:
        pass
