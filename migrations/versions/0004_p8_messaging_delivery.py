"""P8 message delivery tracking and consent.

Revision ID: 0004_p8_messaging_delivery
Revises: 0003_p6_agent_inbox
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_p8_messaging_delivery"
down_revision = "0003_p6_agent_inbox"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "messaging_consents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("whatsapp_opt_out", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sms_opt_out", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "message_deliveries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("daily_message_id", sa.String(length=36), sa.ForeignKey("agent_daily_messages.id", ondelete="SET NULL")),
        sa.Column("agent_id", sa.String(length=36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_reference", sa.String(length=180)),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("error_code", sa.String(length=80)),
        sa.Column("error_message", sa.Text()),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("failed_at", sa.DateTime(timezone=True)),
        sa.Column("callback_payload", sa.Text()),
        sa.UniqueConstraint("provider", "provider_reference", name="uq_message_delivery_provider_ref"),
    )
    op.create_index("ix_message_deliveries_agent_id", "message_deliveries", ["agent_id"])
    op.create_index("ix_message_deliveries_provider_reference", "message_deliveries", ["provider_reference"])
    op.create_index("ix_message_deliveries_status", "message_deliveries", ["status"])
    op.create_index("ix_message_deliveries_next_retry_at", "message_deliveries", ["next_retry_at"])


def downgrade():
    op.drop_index("ix_message_deliveries_next_retry_at", table_name="message_deliveries")
    op.drop_index("ix_message_deliveries_status", table_name="message_deliveries")
    op.drop_index("ix_message_deliveries_provider_reference", table_name="message_deliveries")
    op.drop_index("ix_message_deliveries_agent_id", table_name="message_deliveries")
    op.drop_table("message_deliveries")
    op.drop_table("messaging_consents")
