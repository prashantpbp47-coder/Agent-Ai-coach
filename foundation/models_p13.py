"""P13 business reconciliation, reporting and operational-data models."""
from datetime import date, datetime
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class ExternalBusinessImport(db.Model):
    __tablename__ = "external_business_imports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    import_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(180), index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    agent_code: Mapped[str | None] = mapped_column(String(80), index=True)
    policy_reference: Mapped[str | None] = mapped_column(String(150), index=True)
    premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    raw_row_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "source_name", "source_reference", "policy_reference", name="uq_external_business_row"),)


class OperationalDataRecord(db.Model):
    """Lossless source-row store for booking and renewal operational reports.

    raw_payload preserves every source column. Normalized columns make partner,
    RM, policy, expiry and premium reporting fast without changing source data.
    """
    __tablename__ = "operational_data_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rms.id", ondelete="SET NULL"), index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    source_reference: Mapped[str | None] = mapped_column(String(220), index=True)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    partner_code: Mapped[str | None] = mapped_column(String(80), index=True)
    partner_name: Mapped[str | None] = mapped_column(String(200), index=True)
    rm_code: Mapped[str | None] = mapped_column(String(80), index=True)
    rm_name: Mapped[str | None] = mapped_column(String(200), index=True)
    customer_name: Mapped[str | None] = mapped_column(String(200), index=True)
    customer_mobile: Mapped[str | None] = mapped_column(String(40), index=True)
    product: Mapped[str | None] = mapped_column(String(120), index=True)
    insurer: Mapped[str | None] = mapped_column(String(160), index=True)
    policy_number: Mapped[str | None] = mapped_column(String(180), index=True)
    vehicle_number: Mapped[str | None] = mapped_column(String(40), index=True)
    policy_start_date: Mapped[date | None] = mapped_column(Date, index=True)
    policy_expiry_date: Mapped[date | None] = mapped_column(Date, index=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, index=True)
    premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str | None] = mapped_column(String(80), index=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    imported_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class BusinessReconciliationRun(db.Model):
    __tablename__ = "business_reconciliation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    reconciliation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    tolerance_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tolerance_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    premium_difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policy_difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="mismatch", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class BusinessReconciliationDetail(db.Model):
    __tablename__ = "business_reconciliation_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_reconciliation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    system_policies: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    premium_difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    policy_difference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="mismatch", nullable=False)


class RMDailyReportSnapshot(db.Model):
    __tablename__ = "rm_daily_report_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rm_id: Mapped[str] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    actual_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    projected_premium: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_premium: Mapped[int] = mapped_column(Integer, default=500000, nullable=False)
    active_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calls_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meetings_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_agent_meetings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_value_agents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mismatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("rm_id", "report_date", name="uq_rm_daily_report_snapshot"),)
