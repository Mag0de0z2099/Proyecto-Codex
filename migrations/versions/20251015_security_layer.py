from alembic import op
import sqlalchemy as sa

# ⬇️ Usa EXACTAMENTE este id porque es el que la DB está buscando:
revision = "20251015_security_layer"

# ⬇️ REEMPLAZA esto por el id del head actual de tu repo (ver paso 2):
down_revision = "a20251015_security_layer"

branch_labels = None
depends_on = None

def upgrade():
    # Idempotente para Postgres (no truena si ya existen)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_logins INTEGER DEFAULT 0")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lock_until TIMESTAMP NULL")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(64) NULL")

def downgrade():
    # También idempotente
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS totp_secret")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS lock_until")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS failed_logins")
