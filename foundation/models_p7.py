"""Persistent RM target, marketing and automated agent-message models."""
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class RMDailyBusinessTarget(db.Model):
    __tablename__ = "rm_daily_business_targets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    min_premium: Mapped[int] = mapped_column(Integer, default=300000, nullable=False)
    target_premium: Mapped[int] = mapped_column(Integer, default=500000, nullable=False)
    stretch_premium: Mapped[int] = mapped_column(Integer, default=500000, nullable=False)
    actual_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    projected_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "target_date", name="uq_rm_business_target"),)


class RMMarketingPlan(db.Model):
    __tablename__ = "rm_marketing_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    segment: Mapped[str] = mapped_column(String(80), nullable=False)
    objective: Mapped[str] = mapped_column(String(120), nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_time: Mapped[str | None] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AgentDailyMessage(db.Model):
    __tablename__ = "agent_daily_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    message_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_reference: Mapped[str | None] = mapped_column(String(150))
    dedupe_key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
