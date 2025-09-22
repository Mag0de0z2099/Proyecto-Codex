"""add unique constraint to projects.name"""

from alembic import op
import sqlalchemy as sa


revision = "20251006_projects_unique_name"
down_revision = "20251005_normalize_user_emails"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        conn.execute(
            sa.text(
                """
                WITH dedup AS (
                    SELECT id,
                           ROW_NUMBER() OVER (PARTITION BY name ORDER BY id) AS rn
                      FROM projects
                     WHERE name IS NOT NULL
                )
                UPDATE projects AS p
                   SET name = p.name || '_' || p.id::text
                  FROM dedup
                 WHERE p.id = dedup.id
                   AND dedup.rn > 1
                """
            )
        )
    else:
        conn.execute(
            sa.text(
                """
                UPDATE projects
                   SET name = name || '_' || id
                 WHERE id IN (
                     SELECT id
                       FROM (
                           SELECT id,
                                  ROW_NUMBER() OVER (PARTITION BY name ORDER BY id) AS rn
                             FROM projects
                            WHERE name IS NOT NULL
                       ) AS duplicates
                      WHERE rn > 1
                 )
                """
            )
        )

    try:
        op.create_unique_constraint("uq_projects_name", "projects", ["name"])
    except Exception:
        try:
            op.create_index(
                "uq_projects_name", "projects", ["name"], unique=True
            )
        except Exception:
            pass


def downgrade():
    try:
        op.drop_constraint("uq_projects_name", "projects", type_="unique")
    except Exception:
        try:
            op.drop_index("uq_projects_name", table_name="projects")
        except Exception:
            pass
