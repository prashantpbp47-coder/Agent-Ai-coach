"""Merge repaired legacy migration branches before P19.

This is a no-op schema migration. It explicitly joins the surviving
P7 branch and the P11 branch with the main P18 chain after repairing
broken historical dependency references. No existing migration is
renamed or deleted.
"""
from alembic import op

revision = "0012_migration_graph_repair"
down_revision = (
    "0011_p18_campaign_automation",
    "0006_p11_automation_bi",
    "0004_p7",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
