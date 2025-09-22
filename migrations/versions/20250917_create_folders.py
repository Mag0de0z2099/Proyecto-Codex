"""create folders table (SQLite-safe)"""
from alembic import op
import sqlalchemy as sa

revision = "20250917_create_folders"
down_revision = "20250917_usernames"  # ajusta si tu cadena es distinta
branch_labels = None
depends_on = None


def upgrade():
    # Declarar UNIQUE constraint dentro de create_table para evitar ALTER en SQLite.
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # En SQLite y PostgreSQL, expresamos el default como literal booleano
        sa.Column("is_root", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["parent_id"], ["folders.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("parent_id", "slug", name="uq_folders_parent_slug"),
    )

    # Índices (sí están soportados en SQLite post-creation)
    op.create_index("ix_folders_parent_id", "folders", ["parent_id"], unique=False)
    op.create_index("ix_folders_slug", "folders", ["slug"], unique=False)


def downgrade():
    # Dropear tabla (borra índices asociados automáticamente en SQLite)
    op.drop_table("folders")
