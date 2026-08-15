from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text

# The shared SQLAlchemy instance is imported lazily so this module remains
# compatible with the existing foundation runtime.
from .extensions import db


p19_bp = Blueprint("p19_knowledge", __name__, url_prefix="/api/p19")


class KnowledgeSource(db.Model):
    __tablename__ = "knowledge_sources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False, default="insurance")
    source_type = db.Column(db.String(50), nullable=False, default="internal")
    source_uri = db.Column(db.String(1000), nullable=True)
    version = db.Column(db.String(100), nullable=True)
    effective_from = db.Column(db.DateTime, nullable=True)
    effective_to = db.Column(db.DateTime, nullable=True)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class KnowledgeEntry(db.Model):
    __tablename__ = "knowledge_entries"

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("knowledge_sources.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(120), nullable=False)
    content = db.Column(Text, nullable=False)
    tags = db.Column(db.String(1000), nullable=True)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


@p19_bp.get("/health")
def health():
    return jsonify({"module": "P19", "status": "available"})


@p19_bp.get("/search")
def search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"results": [], "message": "q is required"}), 400

    rows = (
        KnowledgeEntry.query
        .filter_by(approved=True)
        .filter(KnowledgeEntry.content.ilike(f"%{query}%"))
        .limit(10)
        .all()
    )
    return jsonify({
        "results": [
            {"id": r.id, "title": r.title, "topic": r.topic, "content": r.content, "source_id": r.source_id}
            for r in rows
        ]
    })


def register_p19_knowledge(app):
    if "p19_knowledge" not in app.blueprints:
        app.register_blueprint(p19_bp)
    return app
