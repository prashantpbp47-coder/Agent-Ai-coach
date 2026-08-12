"""P0 foundation schema.

Revision ID: 0001_p0_foundation
Revises:
"""

from alembic import op
from foundation.db import db
from foundation import models  # noqa: F401

revision = "0001_p0_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind())


def downgrade():
    db.metadata.drop_all(bind=op.get_bind())
