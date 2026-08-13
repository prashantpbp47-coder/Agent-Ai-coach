"""P16 provider-call audit models."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class AIProviderCall(db.Model):
    __tablename__ = "ai_provider_calls"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), index=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    http_status: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    provider_request_id: Mapped[str | None] = mapped_column(String(180))
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
