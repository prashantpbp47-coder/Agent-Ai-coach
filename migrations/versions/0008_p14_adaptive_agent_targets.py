"""P14 adaptive agent targets and AI-assisted next actions.

Revision ID: 0008_p14_adaptive_agent_targets
Revises: 0007_p13_bi_reconciliation
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_p14_adaptive_agent_targets"
down_revision = "0007_p13_bi_reconciliation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_agent_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_rm_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "club_target_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("club_name", sa.String(120), nullable=False, unique=True),
        sa.Column("target_amount", sa.Integer(), nullable=False),
        sa.Column("minimum_amount", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("maximum_amount", sa.Integer(), nullable=False, server_default="200000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "agent_target_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("target_amount", sa.Integer(), nullable=False),
        sa.Column("visible_to_agent", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rm_total_target_hidden", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("basis", sa.String(50), nullable=False),
        sa.Column("back_record_premium", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tier", sa.String(40), nullable=False),
        sa.Column("club_name", sa.String(120)),
        sa.Column("completion_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("agent_id", "target_date", name="uq_agent_target_date"),
    )
    op.create_index("ix_agent_target_plans_rm_id", "agent_target_plans", ["rm_id"])
    op.create_index("ix_agent_target_plans_agent_id", "agent_target_plans", ["agent_id"])
    op.create_index("ix_agent_target_plans_target_date", "agent_target_plans", ["target_date"])
    op.create_table(
        "agent_target_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("target_plan_id", sa.String(36), sa.ForeignKey("agent_target_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_target_events_target_plan_id", "agent_target_events", ["target_plan_id"])
    op.create_table(
        "agent_nba_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_plan_id", sa.String(36), sa.ForeignKey("agent_target_plans.id", ondelete="SET NULL")),
        sa.Column("recommendation_date", sa.Date(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("suggested_message", sa.Text()),
        sa.Column("follow_up_due_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("outcome", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_nba_recommendations_rm_id", "agent_nba_recommendations", ["rm_id"])
    op.create_index("ix_agent_nba_recommendations_agent_id", "agent_nba_recommendations", ["agent_id"])
    op.create_index("ix_agent_nba_recommendations_recommendation_date", "agent_nba_recommendations", ["recommendation_date"])


def downgrade():
    op.drop_index("ix_agent_nba_recommendations_recommendation_date", table_name="agent_nba_recommendations")
    op.drop_index("ix_agent_nba_recommendations_agent_id", table_name="agent_nba_recommendations")
    op.drop_index("ix_agent_nba_recommendations_rm_id", table_name="agent_nba_recommendations")
    op.drop_table("agent_nba_recommendations")
    op.drop_index("ix_agent_target_events_target_plan_id", table_name="agent_target_events")
    op.drop_table("agent_target_events")
    op.drop_index("ix_agent_target_plans_target_date", table_name="agent_target_plans")
    op.drop_index("ix_agent_target_plans_agent_id", table_name="agent_target_plans")
    op.drop_index("ix_agent_target_plans_rm_id", table_name="agent_target_plans")
    op.drop_table("agent_target_plans")
    op.drop_table("club_target_rules")
    op.drop_table("user_rm_links")
    op.drop_table("user_agent_links")
