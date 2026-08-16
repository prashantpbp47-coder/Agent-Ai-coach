"""P6 agent inbox and document intake schema."""
from alembic import op
from foundation import models_p6

revision = "0003_p6_agent_inbox"
down_revision = "0002_p4_rm_operations"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Create only P6-owned tables.  One-by-one creation avoids SQLAlchemy
    # metadata traversal creating unrelated later-module tables.
    for table in (
        models_p6.InboxThread.__table__,
        models_p6.InboxMessage.__table__,
        models_p6.AgentLeadMessage.__table__,
    ):
        table.create(bind=bind, checkfirst=True)


def downgrade():
    bind = op.get_bind()
    for table in reversed((
        models_p6.AgentLeadMessage.__table__,
        models_p6.InboxMessage.__table__,
        models_p6.InboxThread.__table__,
    )):
        table.drop(bind=bind, checkfirst=True)
