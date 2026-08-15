"""P19 approved insurance knowledge base."""
from alembic import op
import sqlalchemy as sa

revision = "0013_p19_knowledge_base"
down_revision = "0012_migration_graph_repair"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="insurance"),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="internal"),
        sa.Column("source_uri", sa.String(1000)),
        sa.Column("version", sa.String(100)),
        sa.Column("effective_from", sa.DateTime()),
        sa.Column("effective_to", sa.DateTime()),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_knowledge_sources_category", "knowledge_sources", ["category"])
    op.create_index("ix_knowledge_sources_approved", "knowledge_sources", ["approved"])

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("knowledge_sources.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tags", sa.String(1000)),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_knowledge_entries_source_id", "knowledge_entries", ["source_id"])
    op.create_index("ix_knowledge_entries_topic", "knowledge_entries", ["topic"])
    op.create_index("ix_knowledge_entries_approved", "knowledge_entries", ["approved"])


def downgrade():
    op.drop_index("ix_knowledge_entries_approved", table_name="knowledge_entries")
    op.drop_index("ix_knowledge_entries_topic", table_name="knowledge_entries")
    op.drop_index("ix_knowledge_entries_source_id", table_name="knowledge_entries")
    op.drop_table("knowledge_entries")
    op.drop_index("ix_knowledge_sources_approved", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_category", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
