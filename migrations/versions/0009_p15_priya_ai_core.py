"""P15 Priya Insurance AI Core.
Revision ID: 0009_p15_priya_ai_core
Revises: 0008_p14_adaptive_agent_targets
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_p15_priya_ai_core"
down_revision = "0008_p14_adaptive_agent_targets"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("ai_skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("code", name="uq_ai_skills_code"))
    op.create_index("ix_ai_skills_code", "ai_skills", ["code"])
    op.create_index("ix_ai_skills_category", "ai_skills", ["category"])

    op.create_table("ai_knowledge_sources",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("title", sa.String(240), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="internal"),
        sa.Column("source_uri", sa.String(700)), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_ai_knowledge_sources_status", "ai_knowledge_sources", ["status"])

    op.create_table("ai_tasks",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("skill_code", sa.String(80), nullable=False),
        sa.Column("task_type", sa.String(60), nullable=False), sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="SET NULL")),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="SET NULL")),
        sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.id", ondelete="SET NULL")),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="SET NULL")),
        sa.Column("input_json", sa.Text()), sa.Column("output_json", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)))
    for name, column in [("ix_ai_tasks_skill_code","skill_code"),("ix_ai_tasks_agent_id","agent_id"),("ix_ai_tasks_rm_id","rm_id"),("ix_ai_tasks_lead_id","lead_id"),("ix_ai_tasks_policy_id","policy_id"),("ix_ai_tasks_status","status")]: op.create_index(name, "ai_tasks", [column])

    op.create_table("ai_recommendations",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("skill_code", sa.String(80), nullable=False), sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE")),
        sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"), sa.Column("action_type", sa.String(60), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("suggested_message", sa.Text()), sa.Column("source_ids_json", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"), sa.Column("outcome", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)))
    for name, column in [("ix_ai_recommendations_scope","scope"),("ix_ai_recommendations_skill_code","skill_code"),("ix_ai_recommendations_agent_id","agent_id"),("ix_ai_recommendations_rm_id","rm_id"),("ix_ai_recommendations_status","status")]: op.create_index(name, "ai_recommendations", [column])


def downgrade():
    for name in ["ix_ai_recommendations_status","ix_ai_recommendations_rm_id","ix_ai_recommendations_agent_id","ix_ai_recommendations_skill_code","ix_ai_recommendations_scope"]: op.drop_index(name, table_name="ai_recommendations")
    op.drop_table("ai_recommendations")
    for name in ["ix_ai_tasks_status","ix_ai_tasks_policy_id","ix_ai_tasks_lead_id","ix_ai_tasks_rm_id","ix_ai_tasks_agent_id","ix_ai_tasks_skill_code"]: op.drop_index(name, table_name="ai_tasks")
    op.drop_table("ai_tasks")
    op.drop_index("ix_ai_knowledge_sources_status", table_name="ai_knowledge_sources")
    op.drop_table("ai_knowledge_sources")
    op.drop_index("ix_ai_skills_category", table_name="ai_skills")
    op.drop_index("ix_ai_skills_code", table_name="ai_skills")
    op.drop_table("ai_skills")
