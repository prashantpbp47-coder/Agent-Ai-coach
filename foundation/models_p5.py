"""P5 RM visit planning, prospecting and agent referral-link models."""
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow

class AgentVisitPlan(db.Model):
    __tablename__ = "agent_visit_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(30), default="existing", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    area: Mapped[str | None] = mapped_column(String(150), index=True)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "agent_id", "visit_date", name="uq_rm_agent_visit_day"),)

class Prospect(db.Model):
    __tablename__ = "prospects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    area: Mapped[str | None] = mapped_column(String(150), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    profession: Mapped[str | None] = mapped_column(String(150))
    source_url: Mapped[str | None] = mapped_column(String(500))
    evidence: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    suggested_for_date: Mapped[date | None] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class AgentReferralLink(db.Model):
    __tablename__ = "agent_referral_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    destination_url: Mapped[str] = mapped_column(String(500), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class ReferralLead(db.Model):
    __tablename__ = "referral_leads"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    referral_link_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_referral_links.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(200))
    mobile: Mapped[str | None] = mapped_column(String(30), index=True)
    product: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
