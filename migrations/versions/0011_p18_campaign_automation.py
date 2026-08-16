"""P18 campaign automation and inbox action state.
Revision ID: 0011_p18_campaign_automation
Revises: 0010_p16_provider_calls
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_p18_campaign_automation"
down_revision = "0010_p16_provider_calls"
branch_labels = None
depends_on = None


def _table_exists(bind,name): return sa.inspect(bind).has_table(name)
def _index_exists(bind,table,name): return _table_exists(bind,table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind,name,table,cols):
    if _table_exists(bind,table) and not _index_exists(bind,table,name): op.create_index(name,table,cols)


def upgrade():
    bind=op.get_bind()
    if not _table_exists(bind,"messaging_campaigns"):
        op.create_table("messaging_campaigns",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("rm_id",sa.String(36),sa.ForeignKey("rms.id",ondelete="CASCADE")),
            sa.Column("name",sa.String(180),nullable=False),sa.Column("channel",sa.String(30),nullable=False,server_default="whatsapp"),sa.Column("message_template",sa.Text(),nullable=False),
            sa.Column("status",sa.String(30),nullable=False,server_default="draft"),sa.Column("scheduled_at",sa.DateTime(timezone=True)),sa.Column("created_by",sa.String(36),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    for name,cols in (("ix_messaging_campaigns_rm_id",["rm_id"]),("ix_messaging_campaigns_status",["status"]),("ix_messaging_campaigns_scheduled_at",["scheduled_at"])): _index(bind,name,"messaging_campaigns",cols)
    if not _table_exists(bind,"campaign_recipients"):
        op.create_table("campaign_recipients",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("campaign_id",sa.String(36),sa.ForeignKey("messaging_campaigns.id",ondelete="CASCADE"),nullable=False),
            sa.Column("agent_id",sa.String(36),sa.ForeignKey("agents.id",ondelete="CASCADE"),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="pending"),
            sa.Column("rendered_message",sa.Text()),sa.Column("queued_message_id",sa.String(36),sa.ForeignKey("agent_daily_messages.id",ondelete="SET NULL")),sa.Column("error_message",sa.Text()),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("campaign_id","agent_id",name="uq_campaign_recipient"))
    for name,cols in (("ix_campaign_recipients_campaign_id",["campaign_id"]),("ix_campaign_recipients_agent_id",["agent_id"]),("ix_campaign_recipients_status",["status"]),("ix_campaign_recipients_queued_message_id",["queued_message_id"])): _index(bind,name,"campaign_recipients",cols)
    if not _table_exists(bind,"inbox_actions"):
        op.create_table("inbox_actions",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("thread_id",sa.String(36),nullable=False),sa.Column("agent_id",sa.String(36),sa.ForeignKey("agents.id",ondelete="CASCADE")),
            sa.Column("action_type",sa.String(60),nullable=False),sa.Column("suggested_text",sa.Text()),sa.Column("requires_human_approval",sa.Boolean(),nullable=False,server_default=sa.true()),
            sa.Column("status",sa.String(30),nullable=False,server_default="open"),sa.Column("outcome",sa.Text()),sa.Column("created_by",sa.String(36),sa.ForeignKey("users.id",ondelete="SET NULL")),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("completed_at",sa.DateTime(timezone=True)))
    for name,cols in (("ix_inbox_actions_thread_id",["thread_id"]),("ix_inbox_actions_agent_id",["agent_id"]),("ix_inbox_actions_status",["status"])): _index(bind,name,"inbox_actions",cols)


def downgrade():
    bind=op.get_bind()
    for table,indexes in (("inbox_actions",("ix_inbox_actions_status","ix_inbox_actions_agent_id","ix_inbox_actions_thread_id")),("campaign_recipients",("ix_campaign_recipients_queued_message_id","ix_campaign_recipients_status","ix_campaign_recipients_agent_id","ix_campaign_recipients_campaign_id")),("messaging_campaigns",("ix_messaging_campaigns_scheduled_at","ix_messaging_campaigns_status","ix_messaging_campaigns_rm_id"))):
        if _table_exists(bind,table):
            for name in indexes:
                if _index_exists(bind,table,name): op.drop_index(name,table_name=table)
            op.drop_table(table)
