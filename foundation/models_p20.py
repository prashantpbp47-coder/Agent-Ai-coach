"""P20 WhatsApp one-shot quotation intent models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class WhatsAppSession(db.Model):
    __tablename__ = "whatsapp_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    state: Mapped[str] = mapped_column(String(40), default="collecting", nullable=False)
    collected_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("phone", name="uq_whatsapp_session_phone"),)


class WhatsAppEvent(db.Model):
    __tablename__ = "whatsapp_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_message_id: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class WhatsAppQuoteIntent(db.Model):
    __tablename__ = "whatsapp_quote_intents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("whatsapp_sessions.id", ondelete="CASCADE"), index=True)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="collecting", nullable=False, index=True)
    vehicle_number: Mapped[str | None] = mapped_column(String(40))
    customer_name: Mapped[str | None] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(255))
    policy_type: Mapped[str | None] = mapped_column(String(80))
    add_ons: Mapped[str | None] = mapped_column(String(500))
    expiry_date: Mapped[str | None] = mapped_column(String(30))
    rc_attached: Mapped[bool] = mapped_column(default=False, nullable=False)
    policy_attached: Mapped[bool] = mapped_column(default=False, nullable=False)
    normalized_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
