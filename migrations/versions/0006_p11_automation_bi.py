"""P11 automation runs and BI snapshots.

Revision ID: 0006_p11_automation_bi
Revises: 0005_p10_followup_renewal

The legacy runtime can pre-create model metadata before Alembic executes.
P11 therefore preserves existing tables and creates only missing tables and
indexes.
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_p11_automation_bi"
down_revision = "0005_p10_followup_renewal"
branch_labels = None
depends_on = None


def _table_exists(bind, name):
    return sa.inspect(bind).has_table(name)


def _index_exists(bind, table, name):
    if not _table_exists(bind, table):
        return False
    return any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))


def _create_index_if_missing(bind, name, table, columns):
    if _table_exists(bind, table) and not _index_exists(bind, table, name):
        op.create_index(name, table, columns)


def upgrade():
    bind = op.get_bind()

    if not _table_exists(bind, "automation_runs"):
        op.create_table(
            "automation_runs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("run_key", sa.String(180), nullable=False, unique=True),
            sa.Column("run_type", sa.String(50), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("status", sa.String(30), nullable=False, server_default="running"),
            sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error", sa.Text()),
        )
    _create_index_if_missing(bind, "ix_automation_runs_run_key", "automation_runs", ["run_key"])
    _create_index_if_missing(bind, "ix_automation_runs_run_type", "automation_runs", ["run_type"])

    if not _table_exists(bind, "rm_daily_bi_snapshots"):
        op.create_table(
            "rm_daily_bi_snapshots",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="CASCADE"), nullable=False),
            sa.Column("business_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("premium_actual", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("premium_projected", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("renewal_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("new_business_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("active_agents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("existing_meetings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("new_meetings", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("high_value_agents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("calls_completed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_followups", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("target_premium", sa.Integer(), nullable=False, server_default="500000"),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("rm_id", "business_date", name="uq_rm_bi_snapshot"),
        )
    _create_index_if_missing(bind, "ix_rm_daily_bi_snapshots_rm_id", "rm_daily_bi_snapshots", ["rm_id"])
    _create_index_if_missing(bind, "ix_rm_daily_bi_snapshots_business_date", "rm_daily_bi_snapshots", ["business_date"])


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "rm_daily_bi_snapshots"):
        for name in ("ix_rm_daily_bi_snapshots_business_date", "ix_rm_daily_bi_snapshots_rm_id"):
            if _index_exists(bind, "rm_daily_bi_snapshots", name):
                op.drop_index(name, table_name="rm_daily_bi_snapshots")
        op.drop_table("rm_daily_bi_snapshots")
    if _table_exists(bind, "automation_runs"):
        for name in ("ix_automation_runs_run_type", "ix_automation_runs_run_key"):
            if _index_exists(bind, "automation_runs", name):
                op.drop_index(name, table_name="automation_runs")
        op.drop_table("automation_runs")
