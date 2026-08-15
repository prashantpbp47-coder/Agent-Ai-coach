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


def upgrade():
    op.create_table(
        "messaging_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False, server_default="whatsapp"),
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messaging_campaigns_rm_id", "messaging_campaigns", ["rm_id"])
    op.create_index("ix_messaging_campaigns_status", "messaging_campaigns", ["status"])
    op.create_index("ix_messaging_campaigns_scheduled_at", "messaging_campaigns", ["scheduled_at"])

    op.create_table(
        "campaign_recipients",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("messaging_campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("rendered_message", sa.Text()),
        sa.Column("queued_message_id", sa.String(36), sa.ForeignKey("agent_daily_messages.id", ondelete="SET NULL")),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("campaign_id", "agent_id", name="uq_campaign_recipient"),
    )
    op.create_index("ix_campaign_recipients_campaign_id", "campaign_recipients", ["campaign_id"])
    op.create_index("ix_campaign_recipients_agent_id", "campaign_recipients", ["agent_id"])
    op.create_index("ix_campaign_recipients_status", "campaign_recipients", ["status"])
    op.create_index("ix_campaign_recipients_queued_message_id", "campaign_recipients", ["queued_message_id"])

    op.create_table(
        "inbox_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("thread_id", sa.String(36), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE")),
        sa.Column("action_type", sa.String(60), nullable=False),
        sa.Column("suggested_text", sa.Text()),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("outcome", sa.Text()),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_inbox_actions_thread_id", "inbox_actions", ["thread_id"])
    op.create_index("ix_inbox_actions_agent_id", "inbox_actions", ["agent_id"])
    op.create_index("ix_inbox_actions_status", "inbox_actions", ["status"])


def downgrade():
    op.drop_index("ix_inbox_actions_status", table_name="inbox_actions")
    op.drop_index("ix_inbox_actions_agent_id", table_name="inbox_actions")
    op.drop_index("ix_inbox_actions_thread_id", table_name="inbox_actions")
    op.drop_table("inbox_actions")
    op.drop_index("ix_campaign_recipients_queued_message_id", table_name="campaign_recipients")
    op.drop_index("ix_campaign_recipients_status", table_name="campaign_recipients")
    op.drop_index("ix_campaign_recipients_agent_id", table_name="campaign_recipients")
    op.drop_index("ix_campaign_recipients_campaign_id", table_name="campaign_recipients")
    op.drop_table("campaign_recipients")
    op.drop_index("ix_messaging_campaigns_scheduled_at", table_name="messaging_campaigns")
    op.drop_index("ix_messaging_campaigns_status", table_name="messaging_campaigns")
    op.drop_index("ix_messaging_campaigns_rm_id", table_name="messaging_campaigns")
    op.drop_table("messaging_campaigns")
