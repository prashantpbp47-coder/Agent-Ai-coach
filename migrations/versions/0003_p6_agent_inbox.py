"""P6 agent inbox and document intake schema."""
from alembic import op
from foundation.db import db
from foundation import models, models_p5, models_p6

revision = "0003_p6_agent_inbox"
down_revision = "0002_p4_rm_operations"
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind(), tables=[
        models_p6.InboxThread.__table__,
        models_p6.InboxMessage.__table__,
        models_p6.CustomerDocument.__table__,
        models_p6.AgentLeadMessage.__table__,
    ])


def downgrade():
    bind = op.get_bind()
    for table in reversed([models_p6.AgentLeadMessage.__table__, models_p6.CustomerDocument.__table__, models_p6.InboxMessage.__table__, models_p6.InboxThread.__table__]):
        table.drop(bind, checkfirst=True)
