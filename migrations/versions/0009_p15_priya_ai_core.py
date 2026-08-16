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


def _table_exists(bind, name): return sa.inspect(bind).has_table(name)
def _index_exists(bind, table, name): return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind,name,table,cols):
    if _table_exists(bind,table) and not _index_exists(bind,table,name): op.create_index(name,table,cols)


def upgrade():
    bind=op.get_bind()
    if not _table_exists(bind,"ai_skills"):
        op.create_table("ai_skills",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(180),nullable=False),
            sa.Column("category",sa.String(50),nullable=False),sa.Column("description",sa.Text()),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("code",name="uq_ai_skills_code"))
    _index(bind,"ix_ai_skills_code","ai_skills",["code"]); _index(bind,"ix_ai_skills_category","ai_skills",["category"])
    if not _table_exists(bind,"ai_knowledge_sources"):
        op.create_table("ai_knowledge_sources",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("title",sa.String(240),nullable=False),sa.Column("source_type",sa.String(50),nullable=False,server_default="internal"),
            sa.Column("source_uri",sa.String(700)),sa.Column("content",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False,server_default="active"),
            sa.Column("version",sa.Integer(),nullable=False,server_default="1"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    _index(bind,"ix_ai_knowledge_sources_status","ai_knowledge_sources",["status"])
    if not _table_exists(bind,"ai_tasks"):
        op.create_table("ai_tasks",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("skill_code",sa.String(80),nullable=False),sa.Column("task_type",sa.String(60),nullable=False),
            sa.Column("agent_id",sa.String(36),sa.ForeignKey("agents.id",ondelete="SET NULL")),sa.Column("rm_id",sa.String(36),sa.ForeignKey("rms.id",ondelete="SET NULL")),
            sa.Column("lead_id",sa.String(36),sa.ForeignKey("leads.id",ondelete="SET NULL")),sa.Column("policy_id",sa.String(36),sa.ForeignKey("policies.id",ondelete="SET NULL")),
            sa.Column("input_json",sa.Text()),sa.Column("output_json",sa.Text()),sa.Column("status",sa.String(30),nullable=False,server_default="queued"),
            sa.Column("created_by",sa.String(36),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("completed_at",sa.DateTime(timezone=True)))
    for name,col in (("ix_ai_tasks_skill_code","skill_code"),("ix_ai_tasks_agent_id","agent_id"),("ix_ai_tasks_rm_id","rm_id"),("ix_ai_tasks_lead_id","lead_id"),("ix_ai_tasks_policy_id","policy_id"),("ix_ai_tasks_status","status")): _index(bind,name,"ai_tasks",[col])
    if not _table_exists(bind,"ai_recommendations"):
        op.create_table("ai_recommendations",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("scope",sa.String(30),nullable=False),sa.Column("skill_code",sa.String(80),nullable=False),
            sa.Column("agent_id",sa.String(36),sa.ForeignKey("agents.id",ondelete="CASCADE")),sa.Column("rm_id",sa.String(36),sa.ForeignKey("rms.id",ondelete="CASCADE")),
            sa.Column("priority",sa.Integer(),nullable=False,server_default="50"),sa.Column("action_type",sa.String(60),nullable=False),sa.Column("reason",sa.Text(),nullable=False),
            sa.Column("suggested_message",sa.Text()),sa.Column("source_ids_json",sa.Text()),sa.Column("status",sa.String(30),nullable=False,server_default="open"),sa.Column("outcome",sa.Text()),
            sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("completed_at",sa.DateTime(timezone=True)))
    for name,col in (("ix_ai_recommendations_scope","scope"),("ix_ai_recommendations_skill_code","skill_code"),("ix_ai_recommendations_agent_id","agent_id"),("ix_ai_recommendations_rm_id","rm_id"),("ix_ai_recommendations_status","status")): _index(bind,name,"ai_recommendations",[col])


def downgrade():
    bind=op.get_bind()
    for table,indexes in (("ai_recommendations",("ix_ai_recommendations_status","ix_ai_recommendations_rm_id","ix_ai_recommendations_agent_id","ix_ai_recommendations_skill_code","ix_ai_recommendations_scope")),("ai_tasks",("ix_ai_tasks_status","ix_ai_tasks_policy_id","ix_ai_tasks_lead_id","ix_ai_tasks_rm_id","ix_ai_tasks_agent_id","ix_ai_tasks_skill_code")),("ai_knowledge_sources",("ix_ai_knowledge_sources_status",)),("ai_skills",("ix_ai_skills_category","ix_ai_skills_code",))):
        if _table_exists(bind,table):
            for name in indexes:
                if _index_exists(bind,table,name): op.drop_index(name,table_name=table)
            op.drop_table(table)
