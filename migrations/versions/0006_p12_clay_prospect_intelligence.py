"""P12 Clay prospect intelligence.

Revision ID: 0006_p12_clay_prospect_intelligence
Revises: 0005_p10_followup_renewal
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_p12_clay_prospect_intelligence"
down_revision = "0005_p10_followup_renewal"
branch_labels = None
depends_on = None


def _table_exists(bind, name): return sa.inspect(bind).has_table(name)
def _index_exists(bind, table, name):
    return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind, name, table, cols):
    if _table_exists(bind, table) and not _index_exists(bind, table, name): op.create_index(name, table, cols)


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "clay_research_runs"):
        op.create_table(
            "clay_research_runs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("area", sa.String(120)), sa.Column("pincode", sa.String(10)),
            sa.Column("source", sa.String(40), nullable=False, server_default="clay"),
            sa.Column("status", sa.String(30), nullable=False, server_default="received"),
            sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _index(bind, "ix_clay_research_runs_rm_id", "clay_research_runs", ["rm_id"])
    _index(bind, "ix_clay_research_runs_area", "clay_research_runs", ["area"])

    if not _table_exists(bind, "prospect_intelligence"):
        op.create_table(
            "prospect_intelligence",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("prospect_id", sa.String(36), sa.ForeignKey("agent_prospects.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("fit_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("area_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("evidence_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("business_potential_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("relationship_score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recommendation", sa.Text()), sa.Column("research_json", sa.Text()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    _index(bind, "ix_prospect_intelligence_score", "prospect_intelligence", ["score"])

    if not _table_exists(bind, "prospect_source_records"):
        op.create_table(
            "prospect_source_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("prospect_id", sa.String(36), sa.ForeignKey("agent_prospects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("provider", sa.String(40), nullable=False), sa.Column("external_id", sa.String(180)),
            sa.Column("source_url", sa.String(1000)), sa.Column("raw_json", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("provider", "external_id", name="uq_prospect_source_provider_external"),
        )
    _index(bind, "ix_prospect_source_records_prospect_id", "prospect_source_records", ["prospect_id"])
    _index(bind, "ix_prospect_source_records_external_id", "prospect_source_records", ["external_id"])


def downgrade():
    bind = op.get_bind()
    for table, indexes in (
        ("prospect_source_records", ("ix_prospect_source_records_external_id", "ix_prospect_source_records_prospect_id")),
        ("prospect_intelligence", ("ix_prospect_intelligence_score",)),
        ("clay_research_runs", ("ix_clay_research_runs_area", "ix_clay_research_runs_rm_id")),
    ):
        if _table_exists(bind, table):
            for name in indexes:
                if _index_exists(bind, table, name): op.drop_index(name, table_name=table)
            op.drop_table(table)
