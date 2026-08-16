"""P0 foundation schema.

Revision ID: 0001_p0_foundation
Revises:

The runtime imports the complete model set before Alembic starts. The legacy
implementation called ``metadata.create_all()`` against the complete
metadata and therefore pre-created later P4-P19 tables. P0 now owns only the
stable core tables and creates them one-by-one so SQLAlchemy cannot pull in
unrelated tables through metadata traversal.
"""

from alembic import op
from foundation.db import db
from foundation import models  # noqa: F401 - registers base metadata models

revision = "0001_p0_foundation"
down_revision = None
branch_labels = None
depends_on = None


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
    for name in P0_CORE_TABLES:
        table = db.metadata.tables.get(name)
        if table is not None:
            table.create(bind=bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    for name in reversed(P0_CORE_TABLES):
        table = db.metadata.tables.get(name)
        if table is not None:
            table.drop(bind=bind, checkfirst=True)
