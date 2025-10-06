from alembic import op
import sqlalchemy as sa


revision = "a20251016_audit_events"
down_revision = "a20251015_security_layer"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ts", sa.DateTime, nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.Integer, nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("ua", sa.String(256), nullable=True),
        sa.Column("meta", sa.JSON, nullable=True),
    )


def downgrade():
    op.drop_table("audit_events")
