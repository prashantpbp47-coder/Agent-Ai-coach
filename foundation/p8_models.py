"""Persistent P8 outbound messaging delivery state."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow

class MessagingConsent(db.Model):
    __tablename__ = "messaging_consents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), unique=True, nullable=False)
    whatsapp_opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_opt_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class MessageDelivery(db.Model):
    __tablename__ = "message_deliveries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    daily_message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agent_daily_messages.id", ondelete="SET NULL"), index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    callback_payload: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("provider", "provider_reference", name="uq_message_delivery_provider_ref"),)
