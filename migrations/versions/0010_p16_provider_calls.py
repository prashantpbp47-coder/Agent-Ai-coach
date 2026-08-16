"""P16 AI provider call audit ledger.
Revision ID: 0010_p16_provider_calls
Revises: 0009_p15_priya_ai_core
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_p16_provider_calls"
down_revision = "0009_p15_priya_ai_core"
branch_labels = None
depends_on = None


def _table_exists(bind, name): return sa.inspect(bind).has_table(name)
def _index_exists(bind, table, name): return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind,name,table,cols):
    if _table_exists(bind,table) and not _index_exists(bind,table,name): op.create_index(name,table,cols)


def upgrade():
    bind=op.get_bind()
    if not _table_exists(bind,"ai_provider_calls"):
        op.create_table("ai_provider_calls",
            sa.Column("id",sa.String(36),primary_key=True),sa.Column("task_id",sa.String(36),sa.ForeignKey("ai_tasks.id",ondelete="SET NULL")),
            sa.Column("provider",sa.String(30),nullable=False),sa.Column("model",sa.String(120),nullable=False),sa.Column("status",sa.String(30),nullable=False),
            sa.Column("http_status",sa.Integer()),sa.Column("latency_ms",sa.Integer()),sa.Column("input_tokens",sa.Integer()),sa.Column("output_tokens",sa.Integer()),
            sa.Column("provider_request_id",sa.String(180)),sa.Column("error_code",sa.String(100)),sa.Column("error_message",sa.Text()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    _index(bind,"ix_ai_provider_calls_task_id","ai_provider_calls",["task_id"])
    _index(bind,"ix_ai_provider_calls_provider","ai_provider_calls",["provider"])
    _index(bind,"ix_ai_provider_calls_status","ai_provider_calls",["status"])


def downgrade():
    bind=op.get_bind()
    if _table_exists(bind,"ai_provider_calls"):
        for name in ("ix_ai_provider_calls_status","ix_ai_provider_calls_provider","ix_ai_provider_calls_task_id"):
            if _index_exists(bind,"ai_provider_calls",name): op.drop_index(name,table_name="ai_provider_calls")
        op.drop_table("ai_provider_calls")
