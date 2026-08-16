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


def _table_exists(bind, name): return sa.inspect(bind).has_table(name)
def _index_exists(bind, table, name):
    return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind, name, table, cols):
    if _table_exists(bind, table) and not _index_exists(bind, table, name): op.create_index(name, table, cols)


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "user_agent_links"):
        op.create_table("user_agent_links",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    if not _table_exists(bind, "user_rm_links"):
        op.create_table("user_rm_links",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    if not _table_exists(bind, "club_target_rules"):
        op.create_table("club_target_rules",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("club_name", sa.String(120), nullable=False, unique=True),
            sa.Column("target_amount", sa.Integer(), nullable=False),
            sa.Column("minimum_amount", sa.Integer(), nullable=False, server_default="1000"),
            sa.Column("maximum_amount", sa.Integer(), nullable=False, server_default="200000"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    if not _table_exists(bind, "agent_target_plans"):
        op.create_table("agent_target_plans",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("target_date", sa.Date(), nullable=False), sa.Column("target_amount", sa.Integer(), nullable=False),
            sa.Column("visible_to_agent", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("rm_total_target_hidden", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("basis", sa.String(50), nullable=False), sa.Column("back_record_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tier", sa.String(40), nullable=False), sa.Column("club_name", sa.String(120)),
            sa.Column("completion_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("completion_status", sa.String(30), nullable=False, server_default="open"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("agent_id", "target_date", name="uq_agent_target_date"))
    for name, cols in (("ix_agent_target_plans_rm_id",["rm_id"]),("ix_agent_target_plans_agent_id",["agent_id"]),("ix_agent_target_plans_target_date",["target_date"])):
        _index(bind,name,"agent_target_plans",cols)
    if not _table_exists(bind, "agent_target_events"):
        op.create_table("agent_target_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("target_plan_id", sa.String(36), sa.ForeignKey("agent_target_plans.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(40), nullable=False), sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("remarks", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    _index(bind,"ix_agent_target_events_target_plan_id","agent_target_events",["target_plan_id"])
    if not _table_exists(bind, "agent_nba_recommendations"):
        op.create_table("agent_nba_recommendations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("target_plan_id", sa.String(36), sa.ForeignKey("agent_target_plans.id", ondelete="SET NULL")),
            sa.Column("recommendation_date", sa.Date(), nullable=False), sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("action_type", sa.String(50), nullable=False), sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("suggested_message", sa.Text()), sa.Column("follow_up_due_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(30), nullable=False, server_default="open"), sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("outcome", sa.String(100)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for name, cols in (("ix_agent_nba_recommendations_rm_id",["rm_id"]),("ix_agent_nba_recommendations_agent_id",["agent_id"]),("ix_agent_nba_recommendations_recommendation_date",["recommendation_date"])):
        _index(bind,name,"agent_nba_recommendations",cols)


def downgrade():
    bind = op.get_bind()
    for table, indexes in (
        ("agent_nba_recommendations",("ix_agent_nba_recommendations_recommendation_date","ix_agent_nba_recommendations_agent_id","ix_agent_nba_recommendations_rm_id")),
        ("agent_target_events",("ix_agent_target_events_target_plan_id",)),
        ("agent_target_plans",("ix_agent_target_plans_target_date","ix_agent_target_plans_agent_id","ix_agent_target_plans_rm_id")),
        ("club_target_rules",()),("user_rm_links",()),("user_agent_links",()),
    ):
        if _table_exists(bind, table):
            for name in indexes:
                if _index_exists(bind,table,name): op.drop_index(name,table_name=table)
            op.drop_table(table)
