from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from .db import db
from .security import require_role


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
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(1000), nullable=True)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


@p19_bp.get("/health")
def health():
    return jsonify({"module": "P19", "status": "available"})


def _source_payload(source: KnowledgeSource) -> dict:
    return {
        "id": source.id,
        "title": source.title,
        "category": source.category,
        "source_type": source.source_type,
        "source_uri": source.source_uri,
        "version": source.version,
        "effective_from": source.effective_from.isoformat() if source.effective_from else None,
        "effective_to": source.effective_to.isoformat() if source.effective_to else None,
        "approved": bool(source.approved),
    }


def _entry_payload(entry: KnowledgeEntry, source: KnowledgeSource | None = None) -> dict:
    source = source or db.session.get(KnowledgeSource, entry.source_id)
    return {
        "id": entry.id,
        "title": entry.title,
        "topic": entry.topic,
        "content": entry.content,
        "tags": entry.tags,
        "source": _source_payload(source) if source else None,
    }


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_datetime") from exc


@p19_bp.get("/search")
def search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"results": [], "message": "q is required"}), 400

    rows = (
        db.session.query(KnowledgeEntry, KnowledgeSource)
        .join(KnowledgeSource, KnowledgeSource.id == KnowledgeEntry.source_id)
        .filter(KnowledgeEntry.approved.is_(True), KnowledgeSource.approved.is_(True))
        .filter(
            or_(
                KnowledgeEntry.title.ilike(f"%{query}%"),
                KnowledgeEntry.topic.ilike(f"%{query}%"),
                KnowledgeEntry.content.ilike(f"%{query}%"),
                KnowledgeEntry.tags.ilike(f"%{query}%"),
                KnowledgeSource.title.ilike(f"%{query}%"),
            )
        )
        .order_by(KnowledgeSource.effective_from.desc(), KnowledgeEntry.updated_at.desc())
        .limit(20)
        .all()
    )

    results = []
    for entry, source in rows:
        results.append({
            **_entry_payload(entry, source),
            "citation": {
                "source_id": source.id,
                "source_title": source.title,
                "version": source.version,
                "source_uri": source.source_uri,
                "effective_from": source.effective_from.isoformat() if source.effective_from else None,
                "effective_to": source.effective_to.isoformat() if source.effective_to else None,
            },
        })
    return jsonify({"results": results, "count": len(results)})


@p19_bp.get("/sources")
@require_role("ADMIN")
def list_sources():
    rows = KnowledgeSource.query.order_by(KnowledgeSource.created_at.desc()).all()
    return jsonify({"sources": [_source_payload(row) for row in rows]})


@p19_bp.post("/sources")
@require_role("ADMIN")
def create_source():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title_required"}), 400
    try:
        effective_from = _parse_datetime(data.get("effective_from"))
        effective_to = _parse_datetime(data.get("effective_to"))
    except ValueError:
        return jsonify({"error": "invalid_datetime"}), 400
    if effective_to and effective_from and effective_to <= effective_from:
        return jsonify({"error": "effective_to_must_be_after_effective_from"}), 400

    source = KnowledgeSource(
        title=title,
        category=str(data.get("category") or "insurance").strip(),
        source_type=str(data.get("source_type") or "internal").strip(),
        source_uri=data.get("source_uri"),
        version=data.get("version"),
        effective_from=effective_from,
        effective_to=effective_to,
        approved=False,
    )
    db.session.add(source)
    db.session.commit()
    return jsonify(_source_payload(source)), 201


@p19_bp.post("/sources/<int:source_id>/approve")
@require_role("ADMIN")
def approve_source(source_id: int):
    source = db.session.get(KnowledgeSource, source_id)
    if not source:
        return jsonify({"error": "source_not_found"}), 404
    source.approved = True
    db.session.commit()
    return jsonify(_source_payload(source))


@p19_bp.post("/sources/<int:source_id>/ingest")
@require_role("ADMIN")
def ingest_entries(source_id: int):
    source = db.session.get(KnowledgeSource, source_id)
    if not source:
        return jsonify({"error": "source_not_found"}), 404

    data = request.get_json(silent=True) or {}
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        return jsonify({"error": "entries_required"}), 400

    created = []
    for item in entries:
        if not isinstance(item, dict):
            return jsonify({"error": "invalid_entry"}), 400
        title = str(item.get("title") or "").strip()
        topic = str(item.get("topic") or "").strip()
        content = str(item.get("content") or "").strip()
        if not title or not topic or not content:
            return jsonify({"error": "entry_title_topic_content_required"}), 400
        row = KnowledgeEntry(
            source_id=source.id,
            title=title,
            topic=topic,
            content=content,
            tags=item.get("tags"),
            approved=False,
        )
        db.session.add(row)
        created.append(row)

    db.session.commit()
    return jsonify({"source": _source_payload(source), "entries": [_entry_payload(row, source) for row in created]}), 201


@p19_bp.get("/entries")
@require_role("ADMIN")
def list_entries():
    query = (request.args.get("q") or "").strip()
    statement = db.session.query(KnowledgeEntry, KnowledgeSource).join(
        KnowledgeSource, KnowledgeSource.id == KnowledgeEntry.source_id
    )
    if query:
        statement = statement.filter(
            or_(KnowledgeEntry.title.ilike(f"%{query}%"), KnowledgeEntry.topic.ilike(f"%{query}%"))
        )
    rows = statement.order_by(KnowledgeEntry.updated_at.desc()).limit(100).all()
    return jsonify({"entries": [{**_entry_payload(entry, source), "approved": bool(entry.approved)} for entry, source in rows]})


@p19_bp.post("/entries/<int:entry_id>/approve")
@require_role("ADMIN")
def approve_entry(entry_id: int):
    entry = db.session.get(KnowledgeEntry, entry_id)
    if not entry:
        return jsonify({"error": "entry_not_found"}), 404
    source = db.session.get(KnowledgeSource, entry.source_id)
    if not source or not source.approved:
        return jsonify({"error": "source_must_be_approved_first"}), 409
    entry.approved = True
    db.session.commit()
    return jsonify(_entry_payload(entry, source))


def register_p19_knowledge(app):
    if "p19_knowledge" not in app.blueprints:
        app.register_blueprint(p19_bp)
    return app
