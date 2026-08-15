"""Persistent RM operations, hierarchy, daily activity and reconciliation models."""
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow

class AgentHierarchy(db.Model):
    __tablename__ = "agent_hierarchy"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    master_agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class RMDailyTarget(db.Model):
    __tablename__ = "rm_daily_targets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    call_target: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    active_agent_target: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    high_value_agent_target: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    high_value_threshold: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "target_date", name="uq_rm_daily_target"),)

class AgentContact(db.Model):
    __tablename__ = "agent_contacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), default="call", nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), default="contacted", nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    follow_up_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    call_reference: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class AgentDailyActivity(db.Model):
    __tablename__ = "agent_daily_activity"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    active_today: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    projected_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    projected_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    actual_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_contact_outcome: Mapped[str | None] = mapped_column(String(50))
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    projection_remarks: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("agent_id", "activity_date", name="uq_agent_daily_activity"),)

class BusinessEvent(db.Model):
    __tablename__ = "business_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="partnershub", nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(150), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class BusinessReconciliation(db.Model):
    __tablename__ = "business_reconciliation"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    reconciliation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(100), default="external_import", nullable=False)
    source_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policy_difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
