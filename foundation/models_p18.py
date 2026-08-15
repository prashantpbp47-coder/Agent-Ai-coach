"""P18 campaign automation models built on the existing P6/P8 messaging layers."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class MessagingCampaign(db.Model):
    __tablename__ = "messaging_campaigns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), default="whatsapp", nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CampaignRecipient(db.Model):
    __tablename__ = "campaign_recipients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("messaging_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    rendered_message: Mapped[str | None] = mapped_column(Text)
    queued_message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agent_daily_messages.id", ondelete="SET NULL"), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("campaign_id", "agent_id", name="uq_campaign_recipient"),)


class InboxAction(db.Model):
    """Human/AI next-action state for an existing P6 inbox thread."""
    __tablename__ = "inbox_actions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    thread_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)
    suggested_text: Mapped[str | None] = mapped_column(Text)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    outcome: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
