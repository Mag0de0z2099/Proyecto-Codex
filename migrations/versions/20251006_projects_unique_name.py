"""add unique constraint to projects.name"""

from alembic import op
import sqlalchemy as sa


revision = "20251006_projects_unique_name"
down_revision = "20251005_normalize_user_emails"
branch_labels = None
depends_on = None


def _pg_constraint_exists(conn, name: str) -> bool:
    try:
        return bool(
            conn.execute(
                sa.text(
                    """
            SELECT 1
              FROM pg_constraint
             WHERE conname = :name
             LIMIT 1
        """
                ),
                {"name": name},
            ).scalar()
        )
    except Exception:
        return False


def _pg_index_exists(conn, name: str) -> bool:
    try:
        return bool(
            conn.execute(
                sa.text(
                    """
            SELECT 1
              FROM pg_indexes
             WHERE indexname = :name
             LIMIT 1
        """
                ),
                {"name": name},
            ).scalar()
        )
    except Exception:
        return False


def upgrade():
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        conn.execute(
            sa.text(
                "UPDATE projects SET name = NULLIF(BTRIM(name), '') "
                "WHERE name IS NOT NULL"
            )
        )
    else:
        conn.execute(
            sa.text(
                "UPDATE projects SET name = NULLIF(TRIM(name), '') "
                "WHERE name IS NOT NULL"
            )
        )

    if dialect == "postgresql":
        conn.execute(
            sa.text(
                """
            WITH d AS (
                SELECT id, name,
                       ROW_NUMBER() OVER (PARTITION BY name ORDER BY id) AS rn
                  FROM projects
                 WHERE name IS NOT NULL
            )
            UPDATE projects p
               SET name = p.name || '_' || p.id::text
              FROM d
             WHERE p.id = d.id
               AND d.rn > 1
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
               SELECT id FROM (
                 SELECT id,
                        ROW_NUMBER() OVER (PARTITION BY name ORDER BY id) AS rn
                   FROM projects
                  WHERE name IS NOT NULL
               ) t
               WHERE t.rn > 1
             )
        """
            )
        )

    dup_row = conn.execute(
        sa.text(
            """
        SELECT name
          FROM projects
         WHERE name IS NOT NULL
         GROUP BY name
        HAVING COUNT(*) > 1
        LIMIT 1
    """
        )
    ).fetchone()
    if dup_row:
        raise RuntimeError(
            f"[migration 20251006] Aún hay duplicados en projects.name (ej: {dup_row[0]!r}). Revisa desduplicación."
        )

    constraint_name = "uq_projects_name"

    created = False
    if dialect == "postgresql":
        if not _pg_constraint_exists(conn, constraint_name) and not _pg_index_exists(
            conn, constraint_name
        ):
            try:
                op.create_unique_constraint(constraint_name, "projects", ["name"])
                created = True
            except Exception:
                pass
        if not created and not _pg_index_exists(conn, constraint_name):
            try:
                op.create_index(constraint_name, "projects", ["name"], unique=True)
                created = True
            except Exception:
                pass
    else:
        try:
            op.create_index(constraint_name, "projects", ["name"], unique=True)
            created = True
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
