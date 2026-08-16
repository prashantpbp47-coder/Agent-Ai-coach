"""P13 business reconciliation and daily report snapshots.
Revision ID: 0007_p13_bi_reconciliation
Revises: 0006_p12_clay_prospect_intelligence
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_p13_bi_reconciliation"
down_revision = "0006_p12_clay_prospect_intelligence"
branch_labels = None
depends_on = None


def _table_exists(bind, name): return sa.inspect(bind).has_table(name)
def _index_exists(bind, table, name):
    return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))
def _index(bind, name, table, cols):
    if _table_exists(bind, table) and not _index_exists(bind, table, name): op.create_index(name, table, cols)


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "external_business_imports"):
        op.create_table(
            "external_business_imports",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("import_date", sa.Date(), nullable=False),
            sa.Column("source_name", sa.String(120), nullable=False),
            sa.Column("source_reference", sa.String(180)),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("agent_code", sa.String(80)),
            sa.Column("policy_reference", sa.String(150)),
            sa.Column("premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("imported_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("raw_row_json", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("rm_id", "source_name", "source_reference", "policy_reference", name="uq_external_business_row"),
        )
    for name, cols in (
        ("ix_external_business_imports_rm_id", ["rm_id"]),
        ("ix_external_business_imports_import_date", ["import_date"]),
        ("ix_external_business_imports_category", ["category"]),
        ("ix_external_business_imports_agent_code", ["agent_code"]),
        ("ix_external_business_imports_policy_reference", ["policy_reference"]),
    ): _index(bind, name, "external_business_imports", cols)

    if not _table_exists(bind, "business_reconciliation_runs"):
        op.create_table(
            "business_reconciliation_runs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reconciliation_date", sa.Date(), nullable=False),
            sa.Column("source_name", sa.String(120), nullable=False),
            sa.Column("tolerance_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("tolerance_policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source_total", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source_policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("system_total", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("system_policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("premium_difference", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("policy_difference", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(30), nullable=False, server_default="mismatch"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for name, cols in (("ix_business_reconciliation_runs_rm_id", ["rm_id"]),("ix_business_reconciliation_runs_reconciliation_date", ["reconciliation_date"])):
        _index(bind, name, "business_reconciliation_runs", cols)

    if not _table_exists(bind, "business_reconciliation_details"):
        op.create_table(
            "business_reconciliation_details",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("run_id", sa.String(36), sa.ForeignKey("business_reconciliation_runs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("source_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("system_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source_policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("system_policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("premium_difference", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("policy_difference", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(30), nullable=False, server_default="mismatch"),
        )
    for name, cols in (("ix_business_reconciliation_details_run_id", ["run_id"]),("ix_business_reconciliation_details_category", ["category"])):
        _index(bind, name, "business_reconciliation_details", cols)

    if not _table_exists(bind, "rm_daily_report_snapshots"):
        op.create_table(
            "rm_daily_report_snapshots",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("report_date", sa.Date(), nullable=False),
            sa.Column("actual_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("projected_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("target_premium", sa.Integer(), nullable=False, server_default="500000"),
            sa.Column("active_agents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("calls_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("meetings_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("new_agent_meetings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("high_value_agents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mismatch_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("rm_id", "report_date", name="uq_rm_daily_report_snapshot"),
        )
    for name, cols in (("ix_rm_daily_report_snapshots_rm_id", ["rm_id"]),("ix_rm_daily_report_snapshots_report_date", ["report_date"])):
        _index(bind, name, "rm_daily_report_snapshots", cols)


def downgrade():
    bind = op.get_bind()
    for table, indexes in (
        ("rm_daily_report_snapshots", ("ix_rm_daily_report_snapshots_report_date", "ix_rm_daily_report_snapshots_rm_id")),
        ("business_reconciliation_details", ("ix_business_reconciliation_details_category", "ix_business_reconciliation_details_run_id")),
        ("business_reconciliation_runs", ("ix_business_reconciliation_runs_reconciliation_date", "ix_business_reconciliation_runs_rm_id")),
        ("external_business_imports", ("ix_external_business_imports_policy_reference", "ix_external_business_imports_agent_code", "ix_external_business_imports_category", "ix_external_business_imports_import_date", "ix_external_business_imports_rm_id")),
    ):
        if _table_exists(bind, table):
            for name in indexes:
                if _index_exists(bind, table, name): op.drop_index(name, table_name=table)
            op.drop_table(table)
