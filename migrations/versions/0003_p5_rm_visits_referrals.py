"""P5 RM visit planning, prospecting and referral attribution.

Revision ID: 0003_p5_rm_visits_referrals
Revises: 0002_p4_rm_operations
"""
from alembic import op
from foundation.db import db
from foundation import models, models_p4, models_p5  # noqa: F401

revision = "0003_p5_rm_visits_referrals"
down_revision = "0002_p4_rm_operations"
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind())


def downgrade():
    for table in [models_p5.ReferralAttribution.__table__, models_p5.AgentReferralLink.__table__, models_p5.AgentProspect.__table__, models_p5.RMVisitPlan.__table__]:
        table.drop(op.get_bind(), checkfirst=True)
