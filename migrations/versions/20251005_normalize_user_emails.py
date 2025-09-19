"""normalize stored user emails"""

from alembic import op
import sqlalchemy as sa

revision = "20251005_normalize_user_emails"
down_revision = "20250918_add_role_title"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.execute(
        sa.text("UPDATE users SET email = lower(trim(email)) WHERE email IS NOT NULL")
    )

    if dialect == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname = 'uq_users_email_lower'
                ) THEN
                    CREATE UNIQUE INDEX uq_users_email_lower
                        ON users (lower(email))
                        WHERE email IS NOT NULL;
                END IF;
            END$$;
            """
        )


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS uq_users_email_lower;")

    # No se puede restaurar la capitalización original de forma confiable.
