from alembic import op
import sqlalchemy as sa

revision = "a20251015_security_layer"
down_revision = "20251014_alembic_version_64"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_logins INTEGER DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS lock_until TIMESTAMP NULL"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64) NULL"
    )


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS totp_secret")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS lock_until")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS failed_logins")
