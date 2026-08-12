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


def upgrade():
    op.create_table(
        "external_business_imports",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_date", sa.Date(), nullable=False), sa.Column("source_name", sa.String(120), nullable=False), sa.Column("source_reference", sa.String(180)),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("agent_code", sa.String(80)), sa.Column("policy_reference", sa.String(150)),
        sa.Column("premium", sa.Integer(), nullable=False, server_default="0"), sa.Column("policies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("raw_row_json", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("rm_id", "source_name", "source_reference", "policy_reference", name="uq_external_business_row"),
    )
    op.create_index("ix_external_business_imports_rm_id", "external_business_imports", ["rm_id"])
    op.create_index("ix_external_business_imports_import_date", "external_business_imports", ["import_date"])
    op.create_index("ix_external_business_imports_category", "external_business_imports", ["category"])
    op.create_index("ix_external_business_imports_agent_code", "external_business_imports", ["agent_code"])
    op.create_index("ix_external_business_imports_policy_reference", "external_business_imports", ["policy_reference"])

    op.create_table(
        "business_reconciliation_runs",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reconciliation_date", sa.Date(), nullable=False), sa.Column("source_name", sa.String(120), nullable=False),
        sa.Column("tolerance_premium", sa.Integer(), nullable=False, server_default="0"), sa.Column("tolerance_policies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_total", sa.Integer(), nullable=False, server_default="0"), sa.Column("source_policies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("system_total", sa.Integer(), nullable=False, server_default="0"), sa.Column("system_policies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("premium_difference", sa.Integer(), nullable=False, server_default="0"), sa.Column("policy_difference", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="mismatch"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_business_reconciliation_runs_rm_id", "business_reconciliation_runs", ["rm_id"])
    op.create_index("ix_business_reconciliation_runs_reconciliation_date", "business_reconciliation_runs", ["reconciliation_date"])

    op.create_table(
        "business_reconciliation_details",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("run_id", sa.String(36), sa.ForeignKey("business_reconciliation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("source_premium", sa.Integer(), nullable=False, server_default="0"), sa.Column("system_premium", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_policies", sa.Integer(), nullable=False, server_default="0"), sa.Column("system_policies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("premium_difference", sa.Integer(), nullable=False, server_default="0"), sa.Column("policy_difference", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False, server_default="mismatch"),
    )
    op.create_index("ix_business_reconciliation_details_run_id", "business_reconciliation_details", ["run_id"])
    op.create_index("ix_business_reconciliation_details_category", "business_reconciliation_details", ["category"])

    op.create_table(
        "rm_daily_report_snapshots",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False), sa.Column("actual_premium", sa.Integer(), nullable=False, server_default="0"), sa.Column("projected_premium", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_premium", sa.Integer(), nullable=False, server_default="500000"), sa.Column("active_agents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calls_completed", sa.Integer(), nullable=False, server_default="0"), sa.Column("meetings_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_agent_meetings", sa.Integer(), nullable=False, server_default="0"), sa.Column("high_value_agents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mismatch_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("rm_id", "report_date", name="uq_rm_daily_report_snapshot"),
    )
    op.create_index("ix_rm_daily_report_snapshots_rm_id", "rm_daily_report_snapshots", ["rm_id"])
    op.create_index("ix_rm_daily_report_snapshots_report_date", "rm_daily_report_snapshots", ["report_date"])


def downgrade():
    op.drop_index("ix_rm_daily_report_snapshots_report_date", table_name="rm_daily_report_snapshots")
    op.drop_index("ix_rm_daily_report_snapshots_rm_id", table_name="rm_daily_report_snapshots")
    op.drop_table("rm_daily_report_snapshots")
    op.drop_index("ix_business_reconciliation_details_category", table_name="business_reconciliation_details")
    op.drop_index("ix_business_reconciliation_details_run_id", table_name="business_reconciliation_details")
    op.drop_table("business_reconciliation_details")
    op.drop_index("ix_business_reconciliation_runs_reconciliation_date", table_name="business_reconciliation_runs")
    op.drop_index("ix_business_reconciliation_runs_rm_id", table_name="business_reconciliation_runs")
    op.drop_table("business_reconciliation_runs")
    op.drop_index("ix_external_business_imports_policy_reference", table_name="external_business_imports")
    op.drop_index("ix_external_business_imports_agent_code", table_name="external_business_imports")
    op.drop_index("ix_external_business_imports_category", table_name="external_business_imports")
    op.drop_index("ix_external_business_imports_import_date", table_name="external_business_imports")
    op.drop_index("ix_external_business_imports_rm_id", table_name="external_business_imports")
    op.drop_table("external_business_imports")
