"""P4 RM operations schema.

Revision ID: 0002_p4_rm_operations
Revises: 0001_p0_foundation
"""
from alembic import op
from foundation.db import db
from foundation import models_p4  # noqa: F401

revision = "0002_p4_rm_operations"
down_revision = "0001_p0_foundation"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table in (
        models_p4.AgentHierarchy.__table__,
        models_p4.RMDailyTarget.__table__,
        models_p4.AgentContact.__table__,
        models_p4.AgentDailyActivity.__table__,
        models_p4.BusinessEvent.__table__,
        models_p4.BusinessReconciliation.__table__,
    ):
        table.create(bind=bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    for table in reversed((
        models_p4.BusinessReconciliation.__table__,
        models_p4.BusinessEvent.__table__,
        models_p4.AgentDailyActivity.__table__,
        models_p4.AgentContact.__table__,
        models_p4.RMDailyTarget.__table__,
        models_p4.AgentHierarchy.__table__,
    )):
        table.drop(bind=bind, checkfirst=True)
