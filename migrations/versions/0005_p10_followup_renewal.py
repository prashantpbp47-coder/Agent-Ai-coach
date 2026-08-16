"""P10 follow-up and renewal workflow tables.

Revision ID: 0005_p10_followup_renewal
Revises: 0005_p9_document_intelligence

The P0 legacy migration may pre-create SQLAlchemy metadata tables. This
migration therefore creates only missing P10 objects so a fresh database
migration remains safe and idempotent.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_p10_followup_renewal"
down_revision = "0005_p9_document_intelligence"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name):
    return sa.inspect(bind).has_table(table_name)


def _index_exists(bind, table_name, index_name):
    if not _table_exists(bind, table_name):
        return False
    return any(i.get("name") == index_name for i in sa.inspect(bind).get_indexes(table_name))


def _create_index_if_missing(bind, index_name, table_name, columns):
    if _table_exists(bind, table_name) and not _index_exists(bind, table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade():
    bind = op.get_bind()

    if not _table_exists(bind, "renewal_workflows"):
        op.create_table(
            "renewal_workflows",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("expiry_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("stage", sa.String(40), nullable=False, server_default="pending"),
            sa.Column("status", sa.String(30), nullable=False, server_default="open"),
            sa.Column("last_contact_at", sa.DateTime(timezone=True)),
            sa.Column("next_action_at", sa.DateTime(timezone=True)),
            sa.Column("renewed_at", sa.DateTime(timezone=True)),
            sa.Column("renewed_premium", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    _create_index_if_missing(bind, "ix_renewal_workflows_customer_id", "renewal_workflows", ["customer_id"])
    _create_index_if_missing(bind, "ix_renewal_workflows_agent_id", "renewal_workflows", ["agent_id"])
    _create_index_if_missing(bind, "ix_renewal_workflows_expiry_at", "renewal_workflows", ["expiry_at"])
    _create_index_if_missing(bind, "ix_renewal_workflows_next_action_at", "renewal_workflows", ["next_action_at"])

    if not _table_exists(bind, "renewal_reminders"):
        op.create_table(
            "renewal_reminders",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("renewal_id", sa.String(36), sa.ForeignKey("renewal_workflows.id", ondelete="CASCADE"), nullable=False),
            sa.Column("reminder_day", sa.Integer(), nullable=False),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("channel", sa.String(30), nullable=False, server_default="whatsapp"),
            sa.Column("recipient_type", sa.String(20), nullable=False, server_default="agent"),
            sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
            sa.Column("provider_reference", sa.String(180)),
            sa.Column("sent_at", sa.DateTime(timezone=True)),
            sa.Column("error_message", sa.Text()),
            sa.Column("dedupe_key", sa.String(180), nullable=False, unique=True),
        )

    _create_index_if_missing(bind, "ix_renewal_reminders_renewal_id", "renewal_reminders", ["renewal_id"])
    _create_index_if_missing(bind, "ix_renewal_reminders_scheduled_at", "renewal_reminders", ["scheduled_at"])

    if not _table_exists(bind, "follow_up_tasks"):
        op.create_table(
            "follow_up_tasks",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("lead_id", sa.String(36), sa.ForeignKey("leads.id", ondelete="CASCADE")),
            sa.Column("renewal_id", sa.String(36), sa.ForeignKey("renewal_workflows.id", ondelete="CASCADE")),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="SET NULL")),
            sa.Column("rm_id", sa.String(36), sa.ForeignKey("rms.id", ondelete="SET NULL")),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="open"),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
            sa.Column("outcome", sa.String(100)),
            sa.Column("remarks", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    _create_index_if_missing(bind, "ix_follow_up_tasks_lead_id", "follow_up_tasks", ["lead_id"])
    _create_index_if_missing(bind, "ix_follow_up_tasks_renewal_id", "follow_up_tasks", ["renewal_id"])
    _create_index_if_missing(bind, "ix_follow_up_tasks_agent_id", "follow_up_tasks", ["agent_id"])
    _create_index_if_missing(bind, "ix_follow_up_tasks_rm_id", "follow_up_tasks", ["rm_id"])
    _create_index_if_missing(bind, "ix_follow_up_tasks_due_at", "follow_up_tasks", ["due_at"])

    if not _table_exists(bind, "follow_up_events"):
        op.create_table(
            "follow_up_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("task_id", sa.String(36), sa.ForeignKey("follow_up_tasks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(40), nullable=False),
            sa.Column("channel", sa.String(30)),
            sa.Column("provider_reference", sa.String(180)),
            sa.Column("payload_json", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    _create_index_if_missing(bind, "ix_follow_up_events_task_id", "follow_up_events", ["task_id"])


def downgrade():
    bind = op.get_bind()
    for table_name, indexes in (
        ("follow_up_events", [("ix_follow_up_events_task_id",)]),
        ("follow_up_tasks", [("ix_follow_up_tasks_due_at",), ("ix_follow_up_tasks_rm_id",), ("ix_follow_up_tasks_agent_id",), ("ix_follow_up_tasks_renewal_id",), ("ix_follow_up_tasks_lead_id",)]),
        ("renewal_reminders", [("ix_renewal_reminders_scheduled_at",), ("ix_renewal_reminders_renewal_id",)]),
        ("renewal_workflows", [("ix_renewal_workflows_next_action_at",), ("ix_renewal_workflows_expiry_at",), ("ix_renewal_workflows_agent_id",), ("ix_renewal_workflows_customer_id",)]),
    ):
        if _table_exists(bind, table_name):
            for (index_name,) in indexes:
                if _index_exists(bind, table_name, index_name):
                    op.drop_index(index_name, table_name=table_name)
            op.drop_table(table_name)
