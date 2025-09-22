"""add username (unique, not null) and make email nullable (SQLite-safe)"""
from alembic import op
import sqlalchemy as sa

# OJO: actualiza esto si tu down_revision real es otro
revision = "20250917_usernames"
down_revision = "20250916_force_change_pw"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Agregar columna username (temporalmente nullable)
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    # 2) Rellenar username para filas existentes (derivado de email o 'user<ID>')
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        conn.execute(sa.text(
            """
            UPDATE users
               SET username = COALESCE(
                    NULLIF(SPLIT_PART(COALESCE(email, ''), '@', 1), ''),
                    'user' || id::text
               )
             WHERE username IS NULL
            """
        ))
    else:
        conn.execute(sa.text(
            """
            UPDATE users
               SET username = COALESCE(
                    NULLIF(substr(COALESCE(email, ''), 1, instr(COALESCE(email, ''), '@') - 1), ''),
                    'user' || id
               )
             WHERE username IS NULL
            """
        ))

    # 3) En SQLite, cambiar NULLABLE requiere modo batch (recrea tabla bajo el agua)
    with op.batch_alter_table("users", recreate="always") as batch:
        # imponer NOT NULL en username
        batch.alter_column(
            "username",
            existing_type=sa.String(length=64),
            nullable=False,
            existing_nullable=True,
        )
        # hacer email nullable=True (por si antes era NOT NULL)
        batch.alter_column(
            "email",
            existing_type=sa.String(length=254),
            nullable=True,
            existing_nullable=True,  # pon True/False según tu esquema previo; no pasa nada si ya era True
        )
        # agregar UNIQUE sobre username
        batch.create_unique_constraint("uq_users_username", ["username"])


def downgrade():
    # Quitar UNIQUE y el índice/columna (modo batch por compatibilidad)
    with op.batch_alter_table("users", recreate="always") as batch:
        batch.drop_constraint("uq_users_username", type_="unique")
        # si necesitas devolver email a NOT NULL, hazlo aquí
        # batch.alter_column("email", existing_type=sa.String(length=254), nullable=False)

    op.drop_index("ix_users_username", table_name="users")
    op.drop_column("users", "username")
