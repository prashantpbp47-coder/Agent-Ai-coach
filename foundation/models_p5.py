"""P5 RM visit planning, prospecting and referral attribution models."""
from datetime import datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow

class RMVisitPlan(db.Model):
    __tablename__ = "rm_visit_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_type: Mapped[str] = mapped_column(String(30), nullable=False)  # existing/new
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    prospect_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agent_prospects.id", ondelete="SET NULL"), index=True)
    area: Mapped[str | None] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(30), default="planned", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "visit_date", "slot", name="uq_rm_visit_slot"),)

class AgentProspect(db.Model):
    __tablename__ = "agent_prospects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), index=True)
    area: Mapped[str | None] = mapped_column(String(120), index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), index=True)
    profession: Mapped[str | None] = mapped_column(String(150))
    source: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(500))
    evidence: Mapped[str | None] = mapped_column(Text)
    consent_status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="candidate", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class AgentReferralLink(db.Model):
    __tablename__ = "agent_referral_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    destination_url: Mapped[str | None] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class ReferralAttribution(db.Model):
    __tablename__ = "referral_attributions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    referral_link_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_referral_links.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), index=True)
    external_reference: Mapped[str | None] = mapped_column(String(150), index=True)
    attribution_status: Mapped[str] = mapped_column(String(40), default="tracked", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
