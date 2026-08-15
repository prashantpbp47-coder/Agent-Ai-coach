"""Merge repaired legacy P7 branch with the main P18 chain.

This is a no-op data/schema migration. It exists only to make the
historical migration graph explicit after correcting broken dependency
references in P7 and P10. No existing migration is deleted or renamed.
"""
from alembic import op

revision = "0012_migration_graph_repair"
down_revision = ("0011_p18_campaign_automation", "0004_p7")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
