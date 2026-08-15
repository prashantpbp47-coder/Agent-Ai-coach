"""P6 agent inbox and lead-message models.

CustomerDocument is owned by the shared foundation model so P6 and P9 do not
register the same SQLAlchemy table twice.
"""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow, CustomerDocument


class InboxThread(db.Model):
    __tablename__ = "inbox_threads"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    channel: Mapped[str] = mapped_column(String(30), default="whatsapp", nullable=False)
    external_thread_id: Mapped[str | None] = mapped_column(String(150), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class InboxMessage(db.Model):
    __tablename__ = "inbox_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("inbox_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    sender: Mapped[str | None] = mapped_column(String(150))
    message_type: Mapped[str] = mapped_column(String(30), default="text", nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(String(1000))
    external_message_id: Mapped[str | None] = mapped_column(String(150), index=True)
    delivery_status: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class AgentLeadMessage(db.Model):
    __tablename__ = "agent_lead_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id", ondelete="SET NULL"))
    lead_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(30), default="whatsapp", nullable=False)
    intent: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    message_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
