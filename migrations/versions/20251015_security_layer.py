from alembic import op
import sqlalchemy as sa

# ⬇️ Usa EXACTAMENTE este id porque es el que la DB está buscando:
revision = "20251015_security_layer"

# ⬇️ REEMPLAZA esto por el id del head actual de tu repo (ver paso 2):
down_revision = "a20251015_security_layer"

branch_labels = None
depends_on = None

def _has_column(table_name: str, column_name: str) -> bool:
    """Check if ``column_name`` exists on ``table_name`` for the current bind."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade():
    # Idempotente en Postgres y compatible con SQLite: revisamos antes de crear.
    if not _has_column("users", "failed_logins"):
        op.add_column(
            "users",
            sa.Column("failed_logins", sa.Integer(), server_default=sa.text("0")),
        )
        # Opcionalmente retiramos el default para nuevas inserciones automáticas.
        op.alter_column("users", "failed_logins", server_default=None)

    if not _has_column("users", "lock_until"):
        op.add_column("users", sa.Column("lock_until", sa.DateTime(), nullable=True))

    if not _has_column("users", "totp_secret"):
        op.add_column(
            "users",
            sa.Column("totp_secret", sa.String(length=64), nullable=True),
        )


def downgrade():
    # SQLite no soporta DROP COLUMN nativamente, así que lo saltamos.
    if op.get_context().dialect.name == "sqlite":
        return

    if _has_column("users", "totp_secret"):
        op.drop_column("users", "totp_secret")

    if _has_column("users", "lock_until"):
        op.drop_column("users", "lock_until")

    if _has_column("users", "failed_logins"):
        op.drop_column("users", "failed_logins")
