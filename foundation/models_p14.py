"""Adaptive agent targets, visibility links and AI-assisted next actions."""
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class UserAgentLink(db.Model):
    __tablename__ = "user_agent_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class UserRMLink(db.Model):
    __tablename__ = "user_rm_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ClubTargetRule(db.Model):
    __tablename__ = "club_target_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    club_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    target_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_amount: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    maximum_amount: Mapped[int] = mapped_column(Integer, default=200000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentTargetPlan(db.Model):
    __tablename__ = "agent_target_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    target_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    visible_to_agent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rm_total_target_hidden: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    basis: Mapped[str] = mapped_column(String(50), nullable=False)
    back_record_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tier: Mapped[str] = mapped_column(String(40), nullable=False)
    club_name: Mapped[str | None] = mapped_column(String(120))
    completion_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("agent_id", "target_date", name="uq_agent_target_date"),)


class AgentTargetEvent(db.Model):
    __tablename__ = "agent_target_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    target_plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_target_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AgentNBARecommendation(db.Model):
    __tablename__ = "agent_nba_recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    target_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agent_target_plans.id", ondelete="SET NULL"), index=True)
    recommendation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_message: Mapped[str | None] = mapped_column(Text)
    follow_up_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
