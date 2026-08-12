"""P9 document intelligence tables."""
from alembic import op
import sqlalchemy as sa

revision = "0004_p9_document_intelligence"
down_revision = "0003_p6_agent_inbox"
branch_labels = None
 depends_on = None


def upgrade():
    op.create_table(
        "document_extractions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(80)), sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("raw_text", sa.Text()),
        sa.Column("fields_json", sa.Text()), sa.Column("confidence_json", sa.Text()), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_document_extractions_document_id", "document_extractions", ["document_id"])
    op.create_index("ix_document_extractions_status", "document_extractions", ["status"])
    op.create_table(
        "document_verifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False), sa.Column("verified_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("verified_at", sa.DateTime(timezone=True)), sa.Column("corrections_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_verifications_document_id", "document_verifications", ["document_id"])
    op.create_table(
        "vehicle_intelligence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("registration_number", sa.String(40)), sa.Column("owner_name", sa.String(200)), sa.Column("make", sa.String(120)),
        sa.Column("model", sa.String(120)), sa.Column("variant", sa.String(120)), sa.Column("registration_date", sa.String(40)),
        sa.Column("fuel_type", sa.String(50)), sa.Column("chassis_last4", sa.String(10)), sa.Column("engine_last4", sa.String(10)),
        sa.Column("policy_expiry", sa.String(40)), sa.Column("confidence", sa.String(20)), sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vehicle_intelligence_registration_number", "vehicle_intelligence", ["registration_number"])


def downgrade():
    op.drop_index("ix_vehicle_intelligence_registration_number", table_name="vehicle_intelligence")
    op.drop_table("vehicle_intelligence")
    op.drop_index("ix_document_verifications_document_id", table_name="document_verifications")
    op.drop_table("document_verifications")
    op.drop_index("ix_document_extractions_status", table_name="document_extractions")
    op.drop_index("ix_document_extractions_document_id", table_name="document_extractions")
    op.drop_table("document_extractions")
