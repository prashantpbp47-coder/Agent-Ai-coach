"""P12 Clay prospect intelligence and research-run models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class ClayResearchRun(db.Model):
    __tablename__ = "clay_research_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    area: Mapped[str | None] = mapped_column(String(120), index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), index=True)
    source: Mapped[str] = mapped_column(String(40), default="clay", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="received", nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ProspectIntelligence(db.Model):
    __tablename__ = "prospect_intelligence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    prospect_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_prospects.id", ondelete="CASCADE"), nullable=False, unique=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    area_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    business_potential_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationship_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendation: Mapped[str | None] = mapped_column(Text)
    research_json: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ProspectSourceRecord(db.Model):
    __tablename__ = "prospect_source_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    prospect_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_prospects.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(180), index=True)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    raw_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_prospect_source_provider_external"),)
