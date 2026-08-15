"""P7 RM daily target, marketing and agent-message tables."""
from alembic import op
import sqlalchemy as sa

revision = "0004_p7"
down_revision = "0003_p6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("rm_daily_business_targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_date", sa.Date, nullable=False),
        sa.Column("min_premium", sa.Integer, nullable=False, server_default="300000"),
        sa.Column("target_premium", sa.Integer, nullable=False, server_default="500000"),
        sa.Column("stretch_premium", sa.Integer, nullable=False, server_default="500000"),
        sa.Column("actual_premium", sa.Integer, nullable=False, server_default="0"),
        sa.Column("projected_premium", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.UniqueConstraint("rm_id", "target_date", name="uq_rm_business_target"))
    op.create_index("ix_rm_business_target_rm_date", "rm_daily_business_targets", ["rm_id", "target_date"])
    op.create_table("rm_marketing_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_date", sa.Date, nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("segment", sa.String(80), nullable=False),
        sa.Column("objective", sa.String(120), nullable=False),
        sa.Column("message_template", sa.Text, nullable=False),
        sa.Column("scheduled_time", sa.String(10)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()))
    op.create_index("ix_rm_marketing_plan_rm_date", "rm_marketing_plans", ["rm_id", "plan_date"])
    op.create_table("agent_daily_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="SET NULL")),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_date", sa.Date, nullable=False),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("message_type", sa.String(50), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("provider_reference", sa.String(150)),
        sa.Column("dedupe_key", sa.String(150), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_agent_daily_message_agent_date", "agent_daily_messages", ["agent_id", "message_date"])


def downgrade():
    op.drop_table("agent_daily_messages")
    op.drop_index("ix_rm_marketing_plan_rm_date", table_name="rm_marketing_plans")
    op.drop_table("rm_marketing_plans")
    op.drop_index("ix_rm_business_target_rm_date", table_name="rm_daily_business_targets")
    op.drop_table("rm_daily_business_targets")
