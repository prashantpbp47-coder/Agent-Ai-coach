"""Priya Insurance AI Core: skill registry, grounded knowledge and auditable recommendations."""
from datetime import datetime, timezone
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import AuditLog, Agent
from .models_p7 import AgentDailyMessage
from .models_p14 import AgentTargetPlan, UserAgentLink, UserRMLink
from .models_p15 import AIKnowledgeSource, AISkill, AITask, AIRecommendation
from .security import current_user, require_auth, require_role

bp = Blueprint("p15_priya_ai", __name__, url_prefix="/api/p15")

DEFAULT_SKILLS = [
    ("document_intake", "Document Intake", "Read RC/policy inputs and identify missing fields", "document"),
    ("rc_reader", "RC Reader", "Extract and structure vehicle/RC facts for human verification", "document"),
    ("quote_assistant", "Quote Assistant", "Prepare and explain quote inputs without inventing insurer prices", "sales"),
    ("renewal_chaser", "Renewal Chaser", "Prioritize renewal follow-up and prepare messages", "renewal"),
    ("agent_coach", "Agent Coach", "Coach an agent toward the individualized target", "agent"),
    ("rm_coach", "RM Coach", "Surface RM next actions without exposing RM-only targets", "rm"),
    ("prospect_research", "Prospect Research", "Summarize sourced prospect evidence for RM review", "prospecting"),
    ("policy_comparator", "Policy Comparator", "Compare supplied policy and quote facts", "policy"),
    ("claim_intake", "Claim Intake", "Structure claim information for human/insurer review", "claims"),
    ("knowledge_answer", "Knowledge Answer", "Answer from approved, source-grounded insurance knowledge", "knowledge"),
]


def _user_agent_id(user):
    link = db.session.execute(select(UserAgentLink).filter_by(user_id=user.id)).scalar_one_or_none()
    return link.agent_id if link else None


def _user_rm_id(user):
    link = db.session.execute(select(UserRMLink).filter_by(user_id=user.id)).scalar_one_or_none()
    return link.rm_id if link else None


def seed_skills():
    for code, name, description, category in DEFAULT_SKILLS:
        row = db.session.execute(select(AISkill).filter_by(code=code)).scalar_one_or_none()
        if not row:
            db.session.add(AISkill(code=code, name=name, description=description, category=category, is_active=True))
    db.session.commit()


def serialize_rec(row):
    return {
        "id": row.id, "scope": row.scope, "skill_code": row.skill_code,
        "agent_id": row.agent_id, "rm_id": row.rm_id, "priority": row.priority,
        "action_type": row.action_type, "reason": row.reason,
        "suggested_message": row.suggested_message,
        "source_ids": json.loads(row.source_ids_json or "[]"),
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@bp.post("/skills/seed")
@require_role("ADMIN", "RM")
def skills_seed():
    seed_skills()
    rows = db.session.execute(select(AISkill).order_by(AISkill.category, AISkill.code)).scalars().all()
    return jsonify({"skills": [{"code": x.code, "name": x.name, "category": x.category, "active": x.is_active} for x in rows]})


@bp.get("/skills")
@require_auth
def skills_list():
    rows = db.session.execute(select(AISkill).where(AISkill.is_active.is_(True)).order_by(AISkill.category, AISkill.code)).scalars().all()
    return jsonify({"skills": [{"code": x.code, "name": x.name, "category": x.category} for x in rows]})


@bp.post("/knowledge/sources")
@require_role("ADMIN", "RM")
def add_knowledge_source():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()
    if not title or not content:
        return jsonify({"error": "title_and_content_required"}), 400
    row = AIKnowledgeSource(title=title, source_type=data.get("source_type", "internal"), source_uri=data.get("source_uri"), content=content, status="active")
    db.session.add(row)
    db.session.commit()
    return jsonify({"id": row.id, "title": row.title, "source_type": row.source_type, "status": row.status}), 201


@bp.get("/knowledge/sources")
@require_auth
def list_knowledge_sources():
    rows = db.session.execute(select(AIKnowledgeSource).where(AIKnowledgeSource.status == "active").order_by(AIKnowledgeSource.created_at.desc())).scalars().all()
    return jsonify({"sources": [{"id": x.id, "title": x.title, "source_type": x.source_type, "source_uri": x.source_uri} for x in rows]})


@bp.get("/knowledge/search")
@require_auth
def search_knowledge():
    query = str(request.args.get("q", "")).strip().lower()
    if not query:
        return jsonify({"error": "q_required"}), 400
    tokens = [t for t in query.split() if t]
    rows = db.session.execute(select(AIKnowledgeSource).where(AIKnowledgeSource.status == "active").order_by(AIKnowledgeSource.created_at.desc())).scalars().all()
    scored = []
    for row in rows:
        haystack = f"{row.title} {row.content}".lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return jsonify({"query": query, "matches": [{"id": row.id, "title": row.title, "source_type": row.source_type, "source_uri": row.source_uri, "score": score, "excerpt": row.content[:700]} for score, row in scored[:10]]})


@bp.post("/recommendations/generate")
@require_role("RM", "ADMIN")
def generate_recommendations():
    seed_skills()
    user = current_user()
    rm_id = request.args.get("rm_id") or _user_rm_id(user)
    if not rm_id:
        return jsonify({"error": "rm_profile_not_linked"}), 403
    today = datetime.now(timezone.utc).date()
    plans = db.session.execute(select(AgentTargetPlan).where(AgentTargetPlan.rm_id == rm_id, AgentTargetPlan.target_date == today, AgentTargetPlan.completion_status != "completed")).scalars().all()
    rows = []
    for plan in plans:
        agent = db.session.get(Agent, plan.agent_id)
        if not agent:
            continue
        gap = max(plan.target_amount - plan.completion_amount, 0)
        if plan.tier == "reactivation":
            priority, action = 95, "reactivate_agent"
            reason = "Inactive/no-recent-business agent needs a low-friction restart."
            message = f"{agent.name} ji, आज आपका छोटा target ₹{plan.target_amount:,} है. कोई आसान case या renewal हो तो भेजिए, Priya help करेगी."
        elif gap > 0:
            priority = 85 if gap >= plan.target_amount * 0.5 else 70
            action = "completion_push"
            reason = f"₹{gap:,} remains against the individualized target."
            message = f"{agent.name} ji, आपके target में ₹{gap:,} बाकी है. कोई ready customer case/renewal है तो भेजिए."
        else:
            priority, action = 30, "cross_sell"
            reason = "Target complete; look for the next customer opportunity."
            message = f"Great work {agent.name} ji! आज का target complete हुआ. अब अगला customer opportunity देखें."
        source_ids = db.session.execute(select(AIKnowledgeSource.id).where(AIKnowledgeSource.status == "active").limit(5)).scalars().all()
        rec = AIRecommendation(scope="rm", skill_code="agent_coach", agent_id=plan.agent_id, rm_id=rm_id, priority=priority, action_type=action, reason=reason, suggested_message=message, source_ids_json=json.dumps(list(source_ids)), status="open")
        db.session.add(rec)
        rows.append(rec)
    db.session.commit()
    return jsonify({"date": today.isoformat(), "items": [serialize_rec(x) for x in rows]})


@bp.post("/recommendations/<recommendation_id>/queue-message")
@require_role("RM", "ADMIN")
def queue_recommendation_message(recommendation_id):
    user = current_user()
    rec = db.session.get(AIRecommendation, recommendation_id)
    if not rec or rec.status != "open" or not rec.agent_id:
        return jsonify({"error": "open_agent_recommendation_not_found"}), 404
    linked_rm = _user_rm_id(user)
    if linked_rm and rec.rm_id != linked_rm and not any(r.name == "ADMIN" for r in user.roles):
        return jsonify({"error": "forbidden"}), 403
    today = datetime.now(timezone.utc).date()
    dedupe = f"p15:{rec.id}:{today.isoformat()}"
    existing = db.session.execute(select(AgentDailyMessage).filter_by(dedupe_key=dedupe)).scalar_one_or_none()
    if existing:
        return jsonify({"id": existing.id, "status": existing.status, "deduplicated": True})
    msg = AgentDailyMessage(rm_id=rec.rm_id, agent_id=rec.agent_id, message_date=today, channel="whatsapp", message_type=f"priya_{rec.action_type}", body=rec.suggested_message or "", status="queued", dedupe_key=dedupe)
    db.session.add(msg)
    rec.status = "queued_for_delivery"
    db.session.add(AuditLog(action="p15.recommendation.queue_message", user_id=user.id, resource_type="ai_recommendation", resource_id=rec.id, ip_address=request.remote_addr))
    db.session.commit()
    return jsonify({"message_id": msg.id, "recommendation_id": rec.id, "status": msg.status})


@bp.get("/agent/me/recommendations")
@require_auth
def agent_recommendations():
    user = current_user()
    agent_id = _user_agent_id(user)
    if not agent_id:
        return jsonify({"error": "agent_profile_not_linked"}), 403
    rows = db.session.execute(select(AIRecommendation).where(AIRecommendation.agent_id == agent_id, AIRecommendation.scope == "agent", AIRecommendation.status == "open").order_by(AIRecommendation.priority.desc())).scalars().all()
    return jsonify({"items": [serialize_rec(x) for x in rows]})


@bp.post("/tasks")
@require_auth
def create_task():
    user = current_user()
    data = request.get_json(silent=True) or {}
    task = AITask(skill_code=str(data.get("skill_code", "agent_coach")), task_type=str(data.get("task_type", "follow_up")), agent_id=data.get("agent_id"), rm_id=data.get("rm_id"), lead_id=data.get("lead_id"), policy_id=data.get("policy_id"), input_json=json.dumps(data.get("input", {})), status="queued", created_by=user.id)
    db.session.add(task)
    db.session.flush()
    db.session.add(AuditLog(action="p15.ai_task.create", user_id=user.id, resource_type="ai_task", resource_id=task.id, ip_address=request.remote_addr))
    db.session.commit()
    return jsonify({"id": task.id, "status": task.status}), 201


@bp.get("/tasks/<task_id>")
@require_auth
def task_detail(task_id):
    task = db.session.get(AITask, task_id)
    if not task:
        return jsonify({"error": "task_not_found"}), 404
    return jsonify({"id": task.id, "skill_code": task.skill_code, "task_type": task.task_type, "status": task.status, "output": json.loads(task.output_json or "{}"), "created_at": task.created_at.isoformat()})
