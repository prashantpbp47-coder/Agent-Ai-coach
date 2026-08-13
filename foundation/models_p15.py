"""Priya Insurance AI Core models."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import db
from .models import new_id, utcnow


class AISkill(db.Model):
    __tablename__ = "ai_skills"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AIKnowledgeSource(db.Model):
    __tablename__ = "ai_knowledge_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="internal", nullable=False)
    source_uri: Mapped[str | None] = mapped_column(String(700))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AITask(db.Model):
    __tablename__ = "ai_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    skill_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(60), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    rm_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rms.id", ondelete="SET NULL"), index=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("leads.id", ondelete="SET NULL"), index=True)
    policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("policies.id", ondelete="SET NULL"), index=True)
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AIRecommendation(db.Model):
    __tablename__ = "ai_recommendations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scope: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    skill_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    rm_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rms.id", ondelete="CASCADE"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_message: Mapped[str | None] = mapped_column(Text)
    source_ids_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False, index=True)
    outcome: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
