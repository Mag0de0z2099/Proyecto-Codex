from alembic import op
import sqlalchemy as sa

# Este id DEBE ser EXACTAMENTE el que la BD está buscando:
revision = "20251015_security_layer"

# Sustituye por el id que viste en "alembic heads"
down_revision = "a20251015_security_layer"

branch_labels = None
depends_on = None


def upgrade():
    # Idempotente: sólo añade si faltan (seguro en Postgres)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_logins INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lock_until TIMESTAMP NULL")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64) NULL")


def downgrade():
    # Idempotente: sólo elimina si existen
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS totp_secret")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS lock_until")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS failed_logins")
