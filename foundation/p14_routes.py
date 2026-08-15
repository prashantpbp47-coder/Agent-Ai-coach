"""Adaptive per-agent targets and AI-assisted follow-up recommendations."""
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, User
from .models_p4 import BusinessEvent
from .models_p14 import AgentNBARecommendation, AgentTargetEvent, AgentTargetPlan, ClubTargetRule, UserAgentLink, UserRMLLink
from .security import current_user, require_auth, require_role

bp = Blueprint("p14_adaptive_targets", __name__, url_prefix="/api/p14")

MIN_TARGET = 1000
MAX_TARGET = 200000
SMART_TARGET = 19000
RM_TOTAL_TARGET = 500000  # internal RM metric; never returned by agent-facing endpoints.


def _round_1000(value: float) -> int:
    return max(MIN_TARGET, int(round(value / 1000.0) * 1000))


def _agent_stats(agent_id: str, target_date: date):
    start = target_date - timedelta(days=30)
    rows = db.session.execute(select(BusinessEvent.business_date, BusinessEvent.premium).where(BusinessEvent.agent_id == agent_id, BusinessEvent.business_date >= start, BusinessEvent.business_date <= target_date)).all()
    total = sum(int(r.premium or 0) for r in rows)
    days = {r.business_date for r in rows if (r.premium or 0) > 0}
    avg_active_day = (total / len(days)) if days else 0
    return {"total_30d": total, "active_days": len(days), "avg_active_day": avg_active_day}


def _build_target(agent: Agent, target_date: date, club_name: str | None):
    stats = _agent_stats(agent.id, target_date)
    club = None
    if club_name:
        club = db.session.execute(select(ClubTargetRule).filter_by(club_name=club_name, is_active=True)).scalar_one_or_none()
    if club:
        amount = min(max(club.target_amount, club.minimum_amount), club.maximum_amount)
        tier = "club_member"; basis = "club_rule"
    elif agent.status != "active" or stats["total_30d"] == 0:
        amount = MIN_TARGET; tier = "reactivation"; basis = "inactive_or_no_recent_business"
    elif stats["total_30d"] >= SMART_TARGET or stats["avg_active_day"] >= SMART_TARGET:
        amount = min(max(_round_1000(stats["avg_active_day"] * 1.05), SMART_TARGET), MAX_TARGET)
        tier = "smart_agent"; basis = "successful_back_record"
    else:
        amount = min(max(_round_1000(stats["avg_active_day"] * 1.10), MIN_TARGET), MAX_TARGET)
        tier = "adaptive"; basis = "30_day_back_record"
    return amount, tier, basis, stats


def _serialize(plan):
    return {
        "id": plan.id,
        "agent_id": plan.agent_id,
        "target_date": plan.target_date.isoformat(),
        "target_amount": plan.target_amount,
        "completion_amount": plan.completion_amount,
        "remaining_amount": max(plan.target_amount - plan.completion_amount, 0),
        "achievement_percent": round((plan.completion_amount / plan.target_amount) * 100, 1) if plan.target_amount else 0,
        "tier": plan.tier,
        "club_name": plan.club_name,
        "basis": plan.basis,
    }


@bp.post("/admin/link-agent")
@require_role("ADMIN")
def link_agent_user():
    data = request.get_json(silent=True) or {}
    user_id, agent_id = data.get("user_id"), data.get("agent_id")
    if not user_id or not agent_id:
        return jsonify({"error": "user_id_and_agent_id_required"}), 400
    if not db.session.get(User, user_id) or not db.session.get(Agent, agent_id):
        return jsonify({"error": "user_or_agent_not_found"}), 404
    link = db.session.execute(select(UserAgentLink).filter_by(user_id=user_id)).scalar_one_or_none()
    if link:
        link.agent_id = agent_id
    else:
        db.session.add(UserAgentLink(user_id=user_id, agent_id=agent_id))
    db.session.commit()
    return jsonify({"status": "linked", "user_id": user_id, "agent_id": agent_id})


@bp.post("/admin/link-rm")
@require_role("ADMIN")
def link_rm_user():
    data = request.get_json(silent=True) or {}
    user_id, rm_id = data.get("user_id"), data.get("rm_id")
    if not user_id or not rm_id:
        return jsonify({"error": "user_id_and_rm_id_required"}), 400
    if not db.session.get(User, user_id):
        return jsonify({"error": "user_not_found"}), 404
    existing = db.session.execute(select(UserRMLink).filter_by(user_id=user_id)).scalar_one_or_none()
    if existing:
        existing.rm_id = rm_id
    else:
        db.session.add(UserRMLink(user_id=user_id, rm_id=rm_id))
    db.session.commit()
    return jsonify({"status": "linked", "user_id": user_id, "rm_id": rm_id})


@bp.post("/club-rules")
@require_role("RM", "ADMIN")
def club_rule_upsert():
    data = request.get_json(silent=True) or {}
    name = str(data.get("club_name", "")).strip()
    amount = int(data.get("target_amount", 0))
    if not name or amount <= 0:
        return jsonify({"error": "club_name_and_positive_target_required"}), 400
    rule = db.session.execute(select(ClubTargetRule).filter_by(club_name=name)).scalar_one_or_none()
    if not rule:
        rule = ClubTargetRule(club_name=name, target_amount=amount, minimum_amount=MIN_TARGET, maximum_amount=MAX_TARGET)
        db.session.add(rule)
    else:
        rule.target_amount = amount
    rule.minimum_amount = min(max(int(data.get("minimum_amount", rule.minimum_amount)), MIN_TARGET), MAX_TARGET)
    rule.maximum_amount = min(max(int(data.get("maximum_amount", rule.maximum_amount)), rule.minimum_amount), MAX_TARGET)
    db.session.commit()
    return jsonify({"club_name": rule.club_name, "target_amount": rule.target_amount, "minimum_amount": rule.minimum_amount, "maximum_amount": rule.maximum_amount})


@bp.post("/targets/generate")
@require_role("RM", "ADMIN")
def generate_targets():
    data = request.get_json(silent=True) or {}
    target_date = date.fromisoformat(data.get("target_date")) if data.get("target_date") else datetime.now(timezone.utc).date()
    agent_ids = data.get("agent_ids") or []
    club_name = data.get("club_name")
    if not agent_ids:
        rm_id = data.get("rm_id")
        if not rm_id:
            return jsonify({"error": "agent_ids_or_rm_id_required"}), 400
        agent_ids = [a.id for a in db.session.execute(select(Agent).where(Agent.rm_id == rm_id)).scalars().all()]
    generated = []
    for agent_id in agent_ids:
        agent = db.session.get(Agent, agent_id)
        if not agent or not agent.rm_id:
            continue
        amount, tier, basis, stats = _build_target(agent, target_date, club_name)
        plan = db.session.execute(select(AgentTargetPlan).filter_by(agent_id=agent_id, target_date=target_date)).scalar_one_or_none()
        if not plan:
            plan = AgentTargetPlan(rm_id=agent.rm_id, agent_id=agent.id, target_date=target_date, target_amount=amount, basis=basis, back_record_premium=int(stats["total_30d"]), tier=tier, club_name=club_name)
            db.session.add(plan)
        else:
            plan.rm_id = agent.rm_id; plan.target_amount = amount; plan.basis = basis; plan.back_record_premium = int(stats["total_30d"]); plan.tier = tier; plan.club_name = club_name
        generated.append({"agent_id": agent.id, "name": agent.name, "target": amount, "tier": tier, "back_record_30d": int(stats["total_30d"]), "active_days_30d": stats["active_days"]})
    db.session.commit()
    return jsonify({"target_date": target_date.isoformat(), "agent_visible_target_only": True, "items": generated})


@bp.get("/agent/me/target")
@require_auth
def agent_my_target():
    user = current_user()
    link = db.session.execute(select(UserAgentLink).filter_by(user_id=user.id)).scalar_one_or_none()
    if not link:
        return jsonify({"error": "agent_profile_not_linked"}), 403
    target_date = date.fromisoformat(request.args["date"]) if request.args.get("date") else datetime.now(timezone.utc).date()
    plan = db.session.execute(select(AgentTargetPlan).filter_by(agent_id=link.agent_id, target_date=target_date)).scalar_one_or_none()
    if not plan:
        return jsonify({"error": "target_not_generated"}), 404
    return jsonify(_serialize(plan))


@bp.get("/rm/dashboard")
@require_role("RM", "ADMIN")
def rm_dashboard():
    user = current_user(); linked_rm = db.session.execute(select(UserRMLink).filter_by(user_id=user.id)).scalar_one_or_none(); rm_id = request.args.get("rm_id") or (linked_rm.rm_id if linked_rm else None)
    if not rm_id:
        return jsonify({"error": "rm_profile_not_linked"}), 403
    target_date = date.fromisoformat(request.args["date"]) if request.args.get("date") else datetime.now(timezone.utc).date()
    plans = db.session.execute(select(AgentTargetPlan).where(AgentTargetPlan.rm_id == rm_id, AgentTargetPlan.target_date == target_date)).scalars().all()
    total_individual_targets = sum(p.target_amount for p in plans)
    total_completion = sum(p.completion_amount for p in plans)
    return jsonify({"rm_id": rm_id, "date": target_date.isoformat(), "internal_rm_total_target": RM_TOTAL_TARGET, "individual_target_total": total_individual_targets, "completed_total": total_completion, "remaining_individual_target": max(total_individual_targets - total_completion, 0), "items": [_serialize(p) for p in plans]})


@bp.post("/targets/<target_id>/progress")
@require_auth
def target_progress(target_id):
    user = current_user(); plan = db.session.get(AgentTargetPlan, target_id)
    if not plan:
        return jsonify({"error": "target_not_found"}), 404
    is_admin = any(r.name == "ADMIN" for r in user.roles)
    linked_agent = db.session.execute(select(UserAgentLink).filter_by(user_id=user.id, agent_id=plan.agent_id)).scalar_one_or_none()
    linked_rm = db.session.execute(select(UserRMLink).filter_by(user_id=user.id, rm_id=plan.rm_id)).scalar_one_or_none()
    if not (is_admin or linked_agent or linked_rm):
        return jsonify({"error": "forbidden"}), 403
    data = request.get_json(silent=True) or {}
    amount = int(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "positive_amount_required"}), 400
    plan.completion_amount += amount
    plan.completion_status = "completed" if plan.completion_amount >= plan.target_amount else "in_progress"
    db.session.add(AgentTargetEvent(target_plan_id=plan.id, event_type="progress", amount=amount, remarks=data.get("remarks")))
    db.session.commit()
    return jsonify(_serialize(plan))


@bp.post("/nba/generate")
@require_role("RM", "ADMIN")
def generate_nba():
    user = current_user(); linked_rm = db.session.execute(select(UserRMLink).filter_by(user_id=user.id)).scalar_one_or_none(); rm_id = request.args.get("rm_id") or (linked_rm.rm_id if linked_rm else None)
    if not rm_id:
        return jsonify({"error": "rm_profile_not_linked"}), 403
    today = datetime.now(timezone.utc).date()
    plans = db.session.execute(select(AgentTargetPlan).where(AgentTargetPlan.rm_id == rm_id, AgentTargetPlan.target_date == today, AgentTargetPlan.completion_status != "completed")).scalars().all()
    recs = []
    for plan in plans:
        agent = db.session.get(Agent, plan.agent_id)
        if not agent:
            continue
        gap = max(plan.target_amount - plan.completion_amount, 0)
        if plan.tier == "reactivation":
            action = "reactivate_agent"; priority = 95; reason = "Agent is inactive or has no recent business."; message = f"{agent.name} ji, आज ₹{plan.target_amount:,} का छोटा target रखकर फिर से business start करें. कोई case हो तो भेजिए."
        elif gap >= max(5000, int(plan.target_amount * 0.5)):
            action = "priority_followup"; priority = 90; reason = "Large individual target gap remains."; message = f"{agent.name} ji, आपका आज का target ₹{plan.target_amount:,} है और अभी ₹{gap:,} बाकी है. Pending case या renewal share करें."
        else:
            action = "completion_push"; priority = 70; reason = "Target is partially complete; a focused final push is recommended."; message = f"{agent.name} ji, target completion के लिए ₹{gap:,} बाकी है. कोई ready customer case है तो भेजिए."
        rec = AgentNBARecommendation(rm_id=rm_id, agent_id=plan.agent_id, target_plan_id=plan.id, recommendation_date=today, priority=priority, action_type=action, reason=reason, suggested_message=message, follow_up_due_at=datetime.now(timezone.utc) + timedelta(hours=2))
        db.session.add(rec); recs.append(rec)
    db.session.commit()
    return jsonify({"date": today.isoformat(), "recommendations": [{"id": r.id, "agent_id": r.agent_id, "priority": r.priority, "action_type": r.action_type, "reason": r.reason, "suggested_message": r.suggested_message} for r in recs]})


@bp.get("/rm/nba")
@require_role("RM", "ADMIN")
def rm_nba():
    user = current_user(); linked_rm = db.session.execute(select(UserRMLink).filter_by(user_id=user.id)).scalar_one_or_none(); rm_id = request.args.get("rm_id") or (linked_rm.rm_id if linked_rm else None)
    if not rm_id:
        return jsonify({"error": "rm_profile_not_linked"}), 403
    today = date.fromisoformat(request.args["date"]) if request.args.get("date") else datetime.now(timezone.utc).date()
    rows = db.session.execute(select(AgentNBARecommendation).where(AgentNBARecommendation.rm_id == rm_id, AgentNBARecommendation.recommendation_date == today, AgentNBARecommendation.status == "open").order_by(AgentNBARecommendation.priority.desc())).scalars().all()
    return jsonify({"items": [{"id": r.id, "agent_id": r.agent_id, "priority": r.priority, "action_type": r.action_type, "reason": r.reason, "suggested_message": r.suggested_message, "follow_up_due_at": r.follow_up_due_at.isoformat() if r.follow_up_due_at else None} for r in rows]})
