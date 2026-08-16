"""P19 approved insurance knowledge base."""
from alembic import op
import sqlalchemy as sa

revision = "0013_p19_knowledge_base"
down_revision = ("0012_migration_graph_repair", "0003_p5_rm_visits_referrals")
branch_labels = None
depends_on = None


def _table_exists(bind,name): return sa.inspect(bind).has_table(name)
def _index_exists(bind,table,name): return _table_exists(bind,table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind,name,table,cols):
    if _table_exists(bind,table) and not _index_exists(bind,table,name): op.create_index(name,table,cols)


def upgrade():
    bind=op.get_bind()
    if not _table_exists(bind,"knowledge_sources"):
        op.create_table("knowledge_sources",
            sa.Column("id",sa.Integer(),primary_key=True),sa.Column("title",sa.String(255),nullable=False),sa.Column("category",sa.String(100),nullable=False,server_default="insurance"),
            sa.Column("source_type",sa.String(50),nullable=False,server_default="internal"),sa.Column("source_uri",sa.String(1000)),sa.Column("version",sa.String(100)),
            sa.Column("effective_from",sa.DateTime()),sa.Column("effective_to",sa.DateTime()),sa.Column("approved",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("created_at",sa.DateTime(),nullable=False))
    _index(bind,"ix_knowledge_sources_category","knowledge_sources",["category"])
    _index(bind,"ix_knowledge_sources_approved","knowledge_sources",["approved"])
    if not _table_exists(bind,"knowledge_entries"):
        op.create_table("knowledge_entries",
            sa.Column("id",sa.Integer(),primary_key=True),sa.Column("source_id",sa.Integer(),sa.ForeignKey("knowledge_sources.id"),nullable=False),sa.Column("title",sa.String(255),nullable=False),
            sa.Column("topic",sa.String(120),nullable=False),sa.Column("content",sa.Text(),nullable=False),sa.Column("tags",sa.String(1000)),sa.Column("approved",sa.Boolean(),nullable=False,server_default=sa.false()),
            sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False))
    _index(bind,"ix_knowledge_entries_source_id","knowledge_entries",["source_id"])
    _index(bind,"ix_knowledge_entries_topic","knowledge_entries",["topic"])
    _index(bind,"ix_knowledge_entries_approved","knowledge_entries",["approved"])


def downgrade():
    bind=op.get_bind()
    if _table_exists(bind,"knowledge_entries"):
        for name in ("ix_knowledge_entries_approved","ix_knowledge_entries_topic","ix_knowledge_entries_source_id"):
            if _index_exists(bind,"knowledge_entries",name): op.drop_index(name,table_name="knowledge_entries")
        op.drop_table("knowledge_entries")
    if _table_exists(bind,"knowledge_sources"):
        for name in ("ix_knowledge_sources_approved","ix_knowledge_sources_category"):
            if _index_exists(bind,"knowledge_sources",name): op.drop_index(name,table_name="knowledge_sources")
        op.drop_table("knowledge_sources")
