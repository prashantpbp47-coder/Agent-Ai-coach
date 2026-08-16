"""Lossless operational booking/renewal data store for partner reporting."""
from alembic import op
import sqlalchemy as sa

revision = "0014_p13_operational_data"
down_revision = "0013_p19_knowledge_base"
branch_labels = None
depends_on = None


def _table_exists(bind, name):
    return sa.inspect(bind).has_table(name)


def _index_exists(bind, table, name):
    return any(x.get("name") == name for x in sa.inspect(bind).get_indexes(table))


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "operational_data_records"):
        op.create_table(
            "operational_data_records",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="SET NULL"), nullable=True),
            sa.Column("source_type", sa.String(40), nullable=False),
            sa.Column("source_name", sa.String(160), nullable=False),
            sa.Column("source_reference", sa.String(220)),
            sa.Column("row_hash", sa.String(64), nullable=False, unique=True),
            sa.Column("partner_code", sa.String(80)),
            sa.Column("partner_name", sa.String(200)),
            sa.Column("rm_code", sa.String(80)),
            sa.Column("rm_name", sa.String(200)),
            sa.Column("customer_name", sa.String(200)),
            sa.Column("customer_mobile", sa.String(40)),
            sa.Column("product", sa.String(120)),
            sa.Column("insurer", sa.String(160)),
            sa.Column("policy_number", sa.String(180)),
            sa.Column("vehicle_number", sa.String(40)),
            sa.Column("policy_start_date", sa.Date()),
            sa.Column("policy_expiry_date", sa.Date()),
            sa.Column("transaction_date", sa.Date()),
            sa.Column("premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("policies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(80)),
            sa.Column("raw_payload", sa.Text(), nullable=False),
            sa.Column("imported_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        )
    for name, cols in {
        "ix_operational_source_type": ["source_type"],
        "ix_operational_source_name": ["source_name"],
        "ix_operational_partner_code": ["partner_code"],
        "ix_operational_partner_name": ["partner_name"],
        "ix_operational_rm_code": ["rm_code"],
        "ix_operational_policy_number": ["policy_number"],
        "ix_operational_vehicle_number": ["vehicle_number"],
        "ix_operational_expiry": ["policy_expiry_date"],
        "ix_operational_transaction_date": ["transaction_date"],
    }.items():
        if not _index_exists(bind, "operational_data_records", name):
            op.create_index(name, "operational_data_records", cols)


def downgrade():
    bind = op.get_bind()
    if _table_exists(bind, "operational_data_records"):
        for name in (
            "ix_operational_source_type",
            "ix_operational_source_name",
            "ix_operational_partner_code",
            "ix_operational_partner_name",
            "ix_operational_rm_code",
            "ix_operational_policy_number",
            "ix_operational_vehicle_number",
            "ix_operational_expiry",
            "ix_operational_transaction_date",
        ):
            if _index_exists(bind, "operational_data_records", name):
                op.drop_index(name, table_name="operational_data_records")
        op.drop_table("operational_data_records")
