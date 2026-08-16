"""P20 WhatsApp one-shot quotation state and event storage."""
from alembic import op
import sqlalchemy as sa

revision = "0015_p20_whatsapp_one_shot"
down_revision = "0014_p13_operational_data"
branch_labels = None
depends_on = None


def _table_exists(bind, name):
    return sa.inspect(bind).has_table(name)


def _index_exists(bind, table, name):
    return _table_exists(bind, table) and any(i.get("name") == name for i in sa.inspect(bind).get_indexes(table))


def upgrade():
    bind = op.get_bind()
    if not _table_exists(bind, "whatsapp_sessions"):
        op.create_table(
            "whatsapp_sessions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("phone", sa.String(40), nullable=False),
            sa.Column("agent_id", sa.String(36), sa.ForeignKey("agents.id", ondelete="SET NULL")),
            sa.Column("state", sa.String(40), nullable=False, server_default="collecting"),
            sa.Column("collected_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("phone", name="uq_whatsapp_session_phone"),
        )
    if not _table_exists(bind, "whatsapp_events"):
        op.create_table(
            "whatsapp_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("external_message_id", sa.String(180), nullable=False, unique=True),
            sa.Column("phone", sa.String(40), nullable=False),
            sa.Column("direction", sa.String(20), nullable=False),
            sa.Column("body", sa.Text(), nullable=False, server_default=""),
            sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    if not _table_exists(bind, "whatsapp_quote_intents"):
        op.create_table(
            "whatsapp_quote_intents",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("session_id", sa.String(36), sa.ForeignKey("whatsapp_sessions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("phone", sa.String(40), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="collecting"),
            sa.Column("vehicle_number", sa.String(40)),
            sa.Column("customer_name", sa.String(200)),
            sa.Column("email", sa.String(255)),
            sa.Column("policy_type", sa.String(80)),
            sa.Column("add_ons", sa.String(500)),
            sa.Column("expiry_date", sa.String(30)),
            sa.Column("rc_attached", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("policy_attached", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("normalized_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("raw_text", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    for name, table, cols in (
        ("ix_whatsapp_sessions_phone", "whatsapp_sessions", ["phone"]),
        ("ix_whatsapp_sessions_agent_id", "whatsapp_sessions", ["agent_id"]),
        ("ix_whatsapp_events_phone", "whatsapp_events", ["phone"]),
        ("ix_whatsapp_quote_intents_session_id", "whatsapp_quote_intents", ["session_id"]),
        ("ix_whatsapp_quote_intents_phone", "whatsapp_quote_intents", ["phone"]),
        ("ix_whatsapp_quote_intents_status", "whatsapp_quote_intents", ["status"]),
    ):
        if not _index_exists(bind, table, name):
            op.create_index(name, table, cols)


def downgrade():
    bind = op.get_bind()
    for table, indexes in (
        ("whatsapp_quote_intents", ("ix_whatsapp_quote_intents_status", "ix_whatsapp_quote_intents_phone", "ix_whatsapp_quote_intents_session_id")),
        ("whatsapp_events", ("ix_whatsapp_events_phone",)),
        ("whatsapp_sessions", ("ix_whatsapp_sessions_agent_id", "ix_whatsapp_sessions_phone")),
    ):
        if _table_exists(bind, table):
            for name in indexes:
                if _index_exists(bind, table, name): op.drop_index(name, table_name=table)
            op.drop_table(table)
