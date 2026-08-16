"""P0 foundation schema.

Revision ID: 0001_p0_foundation
Revises:

The runtime imports the complete model set before Alembic starts.  The
original implementation used ``db.metadata.create_all()`` which therefore
pre-created P4-P19 tables and caused later migrations to collide with already
existing objects on a fresh database.

P0 owns only the stable core tables below.  Later migrations own their own
module tables and may safely create them when their revision runs.
"""

from alembic import op
from foundation.db import db
from foundation import models  # noqa: F401 - registers base metadata models

revision = "0001_p0_foundation"
down_revision = None
branch_labels = None
depends_on = None


# Tables that belong to the original platform foundation.  Future-module
# tables are deliberately excluded so their Alembic revisions remain the
# single owner of those schema objects.
P0_CORE_TABLES = (
    "users",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "rms",
    "agents",
    "customers",
    "leads",
    "quotes",
    "policies",
    "renewals",
    "follow_ups",
    "ai_conversations",
    "audit_logs",
)


def upgrade():
    bind = op.get_bind()
    tables = [
        db.metadata.tables[name]
        for name in P0_CORE_TABLES
        if name in db.metadata.tables
    ]
    db.metadata.create_all(bind=bind, tables=tables, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    tables = [
        db.metadata.tables[name]
        for name in reversed(P0_CORE_TABLES)
        if name in db.metadata.tables
    ]
    for table in tables:
        table.drop(bind=bind, checkfirst=True)
