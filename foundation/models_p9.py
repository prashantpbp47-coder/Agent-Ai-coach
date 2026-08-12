"""P9 document/OCR intelligence models.

The OCR engine is provider-neutral. Extracted fields remain unverified until
an explicit human verification action is recorded.
"""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class DocumentExtraction(db.Model):
    __tablename__ = "document_extractions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str | None] = mapped_column(String(80))
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    raw_text: Mapped[str | None] = mapped_column(Text)
    fields_json: Mapped[str | None] = mapped_column(Text)
    confidence_json: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentVerification(db.Model):
    __tablename__ = "document_verifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    corrections_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class VehicleIntelligence(db.Model):
    __tablename__ = "vehicle_intelligence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("customer_documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    registration_number: Mapped[str | None] = mapped_column(String(40), index=True)
    owner_name: Mapped[str | None] = mapped_column(String(200))
    make: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    variant: Mapped[str | None] = mapped_column(String(120))
    registration_date: Mapped[str | None] = mapped_column(String(40))
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    chassis_last4: Mapped[str | None] = mapped_column(String(10))
    engine_last4: Mapped[str | None] = mapped_column(String(10))
    policy_expiry: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[str | None] = mapped_column(String(20))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
