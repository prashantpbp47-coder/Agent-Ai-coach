"""P11 automation runs and BI snapshot models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow

class AutomationRun(db.Model):
    __tablename__ = "automation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_key: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="running", nullable=False)
    processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)

class RMDailyBISnapshot(db.Model):
    __tablename__ = "rm_daily_bi_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    business_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    premium_actual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    premium_projected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    renewal_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_business_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    existing_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_value_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calls_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_followups: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_premium: Mapped[int] = mapped_column(Integer, default=500000, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "business_date", name="uq_rm_bi_snapshot"),)
