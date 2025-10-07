"""merge heads

Revision ID: a76a13d31500
Revises: 20251015_security_layer, a20251016_audit_events
Create Date: 2025-10-07 14:48:23.001817

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a76a13d31500'
down_revision = ('20251015_security_layer', 'a20251016_audit_events')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
