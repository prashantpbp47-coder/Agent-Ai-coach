"""Persistent follow-up and renewal workflow models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class RenewalWorkflow(db.Model):
    __tablename__ = "renewal_workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, unique=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    expiry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    renewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewed_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class RenewalReminder(db.Model):
    __tablename__ = "renewal_reminders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    renewal_id: Mapped[str] = mapped_column(String(36), ForeignKey("renewal_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_day: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), default="whatsapp", nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(20), default="agent", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(180))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)


class FollowUpTask(db.Model):
    __tablename__ = "follow_up_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lead_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    renewal_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("renewal_workflows.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    rm_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rms.id", ondelete="SET NULL"), index=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(100))
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class FollowUpEvent(db.Model):
    __tablename__ = "follow_up_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("follow_up_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(30))
    provider_reference: Mapped[str | None] = mapped_column(String(180))
    payload_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
