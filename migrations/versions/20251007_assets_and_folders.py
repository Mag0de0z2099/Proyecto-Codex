"""folders overhaul and assets table"""

from alembic import op
import sqlalchemy as sa


revision = "20251007_assets_and_folders"
down_revision = "20251006_projects_unique_name"
branch_labels = None
depends_on = None


def upgrade():
    # Drop legacy folders table if it exists from older schema revisions.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "folders" in inspector.get_table_names():
        op.drop_table("folders")

    op.create_table(
        "folders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("logical_path", sa.String(512), nullable=False),
        sa.Column("fs_path", sa.String(1024), nullable=False),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.UniqueConstraint(
            "project_id",
            "logical_path",
            name="uq_folder_project_path",
        ),
    )
    op.create_index("ix_folders_project_id", "folders", ["project_id"])

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "folder_id",
            sa.Integer,
            sa.ForeignKey("folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("relative_path", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.UniqueConstraint(
            "project_id",
            "folder_id",
            "relative_path",
            name="uq_asset_scope_path",
        ),
    )
    op.create_index("ix_assets_project_id", "assets", ["project_id"])
    op.create_index("ix_assets_folder_id", "assets", ["folder_id"])
    op.create_index("ix_assets_sha256", "assets", ["sha256"])


def downgrade():
    op.drop_index("ix_assets_sha256", table_name="assets")
    op.drop_index("ix_assets_folder_id", table_name="assets")
    op.drop_index("ix_assets_project_id", table_name="assets")
    op.drop_table("assets")

    op.drop_index("ix_folders_project_id", table_name="folders")
    op.drop_table("folders")
