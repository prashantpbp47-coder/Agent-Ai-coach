"""P5 RM visit planner, area-aware prospecting and agent referral links."""
import secrets
import uuid
from datetime import date, timedelta
from urllib.parse import urlparse

from flask import Blueprint, Response, jsonify, redirect, request
from sqlalchemy import func, select

from .db import db
from .models import Agent, Customer, Lead, RM
from .models_p5 import AgentProspect, AgentReferralLink, ReferralAttribution, RMVisitPlan
from .security import current_user, require_permission, require_role

bp = Blueprint("p5", __name__, url_prefix="/api/p5")


def audit(action, resource_type, resource_id=None):
    from .models import AuditLog
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=resource_type, resource_id=resource_id,
                            user_id=u.id if u else None, request_id=str(uuid.uuid4()), ip_address=request.remote_addr))


def rm_for_user():
    u = current_user()
    if not u:
        return None
    return db.session.execute(select(RM).filter(func.lower(RM.email) == func.lower(u.email))).scalar_one_or_none()


def rm_scope():
    requested = request.args.get("rm_id") or (request.get_json(silent=True) or {}).get("rm_id")
    rm = rm_for_user()
    is_admin = any(r.name == "ADMIN" for r in getattr(current_user(), "roles", []))
    if requested and rm and requested != rm.id and not is_admin:
        return None
    return requested or (rm.id if rm else None)


def nearest_existing(rm_id, area, exclude_ids):
    q = select(Agent).where(Agent.rm_id == rm_id, Agent.status == "active")
    if area:
        q = q.order_by(func.lower(func.coalesce(Agent.city, "")) == area.lower().replace(" ", ""))
    agents = db.session.execute(q).scalars().all()
    available = [a for a in agents if a.id not in exclude_ids]
    return available


@bp.post("/visit-plan/generate")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def generate_visit_plan():
    data = request.get_json(silent=True) or {}
    rm_id = rm_scope()
    visit_date = date.fromisoformat(data["visit_date"]) if data.get("visit_date") else date.today()
    area = str(data.get("area") or "").strip() or None
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422
    existing = db.session.execute(select(RMVisitPlan).where(RMVisitPlan.rm_id == rm_id, RMVisitPlan.visit_date == visit_date).order_by(RMVisitPlan.slot)).scalars().all()
    if existing:
        return jsonify({"date": str(visit_date), "rm_id": rm_id, "reused": True, "plan": [serialize_plan(x) for x in existing]})

    excluded = set()
    rows = []
    # 3 existing agents: prefer same-area records, but fall back to active agents.
    existing_agents = nearest_existing(rm_id, area, excluded)
    for slot, agent in enumerate(existing_agents[:3], start=1):
        row = RMVisitPlan(rm_id=rm_id, visit_date=visit_date, slot=slot, plan_type="existing", agent_id=agent.id, area=area or agent.city)
        db.session.add(row); rows.append(row); excluded.add(agent.id)

    # 2 new prospects: prefer same area and never schedule the same prospect twice within 7 days.
    cutoff = visit_date - timedelta(days=7)
    recent = set(db.session.execute(select(RMVisitPlan.prospect_id).where(RMVisitPlan.rm_id == rm_id, RMVisitPlan.prospect_id.is_not(None), RMVisitPlan.visit_date >= cutoff)).scalars().all())
    prospects_q = select(AgentProspect).where(AgentProspect.rm_id == rm_id, AgentProspect.status == "candidate", AgentProspect.id.not_in(recent))
    if area:
        prospects_q = prospects_q.order_by(func.lower(func.coalesce(AgentProspect.area, "")) == area.lower())
    prospects = db.session.execute(prospects_q).scalars().all()
    for slot, prospect in enumerate(prospects[:2], start=4):
        row = RMVisitPlan(rm_id=rm_id, visit_date=visit_date, slot=slot, plan_type="new", prospect_id=prospect.id, area=prospect.area or area)
        db.session.add(row); rows.append(row)
    for row in rows:
        audit("rm.visit_plan.create", "rm_visit_plan", row.id)
    db.session.commit()
    return jsonify({"date": str(visit_date), "rm_id": rm_id, "area": area, "plan": [serialize_plan(x) for x in rows]})


def serialize_plan(row):
    item = {"id": row.id, "slot": row.slot, "type": row.plan_type, "area": row.area, "status": row.status}
    if row.agent_id:
        a = db.session.get(Agent, row.agent_id)
        item.update({"agent_id": a.id, "partner_code": a.partner_code, "name": a.name, "phone": a.phone, "city": a.city})
    if row.prospect_id:
        p = db.session.get(AgentProspect, row.prospect_id)
        item.update({"prospect_id": p.id, "name": p.name, "phone": p.phone, "profession": p.profession, "source": p.source, "source_url": p.source_url, "consent_status": p.consent_status})
    return item


@bp.get("/visit-plan")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def get_visit_plan():
    rm_id = rm_scope()
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422
    d = date.fromisoformat(request.args.get("date")) if request.args.get("date") else date.today()
    rows = db.session.execute(select(RMVisitPlan).where(RMVisitPlan.rm_id == rm_id, RMVisitPlan.visit_date == d).order_by(RMVisitPlan.slot)).scalars().all()
    return jsonify({"date": str(d), "rm_id": rm_id, "count": len(rows), "plan": [serialize_plan(x) for x in rows]})


@bp.post("/prospects")
@require_permission("agents:write")
def add_prospect():
    data = request.get_json(silent=True) or {}
    rm_id = rm_scope()
    if not rm_id or not data.get("name"):
        return jsonify({"error": "rm_mapping_and_name_required"}), 400
    source_url = data.get("source_url")
    if source_url:
        parsed = urlparse(source_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            return jsonify({"error": "invalid_source_url"}), 400
    p = AgentProspect(rm_id=rm_id, name=str(data["name"]).strip(), phone=data.get("phone"), area=data.get("area"), pincode=data.get("pincode"), profession=data.get("profession"), source=data.get("source"), source_url=source_url, evidence=data.get("evidence"), consent_status=data.get("consent_status", "unknown"), status=data.get("status", "candidate"))
    db.session.add(p); db.session.flush(); audit("rm.prospect.create", "agent_prospect", p.id); db.session.commit()
    return jsonify({"id": p.id, "name": p.name, "area": p.area, "source": p.source, "consent_status": p.consent_status}), 201


@bp.get("/prospects")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def list_prospects():
    rm_id = rm_scope()
    area = request.args.get("area")
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422
    q = select(AgentProspect).where(AgentProspect.rm_id == rm_id)
    if area:
        q = q.where(func.lower(AgentProspect.area) == area.lower())
    rows = db.session.execute(q.order_by(AgentProspect.created_at.desc())).scalars().all()
    return jsonify({"items": [{"id": p.id, "name": p.name, "phone": p.phone, "area": p.area, "pincode": p.pincode, "profession": p.profession, "source": p.source, "source_url": p.source_url, "consent_status": p.consent_status, "status": p.status} for p in rows]})


@bp.post("/referral-links")
@require_permission("agents:write")
def create_referral_link():
    data = request.get_json(silent=True) or {}
    agent = db.session.get(Agent, data.get("agent_id"))
    if not agent:
        return jsonify({"error": "agent_not_found"}), 404
    row = db.session.execute(select(AgentReferralLink).filter_by(agent_id=agent.id)).scalar_one_or_none()
    if not row:
        slug = f"{agent.partner_code}-{secrets.token_urlsafe(6)}"
        row = AgentReferralLink(agent_id=agent.id, slug=slug, destination_url=data.get("destination_url"), is_active=True)
        db.session.add(row)
    else:
        row.destination_url = data.get("destination_url", row.destination_url)
        row.is_active = True
    db.session.flush(); audit("agent.referral_link.create", "agent_referral_link", row.id); db.session.commit()
    return jsonify({"agent_id": agent.id, "partner_code": agent.partner_code, "slug": row.slug, "url": f"/r/{row.slug}", "destination_url": row.destination_url}), 201


@bp.get("/referral-links/<agent_id>")
@require_permission("agents:read")
def get_referral_link(agent_id):
    row = db.session.execute(select(AgentReferralLink).filter_by(agent_id=agent_id)).scalar_one_or_none()
    if not row:
        return jsonify({"error": "referral_link_not_found"}), 404
    return jsonify({"agent_id": agent_id, "slug": row.slug, "url": f"/r/{row.slug}", "destination_url": row.destination_url, "clicks": row.clicks, "leads": row.leads, "policies": row.policies, "premium": row.premium, "active": row.is_active})


@bp.post("/referral-links/<agent_id>/deactivate")
@require_permission("agents:write")
def deactivate_referral(agent_id):
    row = db.session.execute(select(AgentReferralLink).filter_by(agent_id=agent_id)).scalar_one_or_none()
    if not row:
        return jsonify({"error": "referral_link_not_found"}), 404
    row.is_active = False; audit("agent.referral_link.deactivate", "agent_referral_link", row.id); db.session.commit()
    return jsonify({"deactivated": True})


@bp.get("/referrals/<slug>")
def public_referral(slug):
    row = db.session.execute(select(AgentReferralLink).filter_by(slug=slug, is_active=True)).scalar_one_or_none()
    if not row:
        return jsonify({"error": "referral_not_found"}), 404
    row.clicks += 1
    # Destination is only an explicit configured external provider URL; otherwise leave the visitor in PartnersHub.
    target = row.destination_url
    db.session.commit()
    if target:
        parsed = urlparse(target)
        if parsed.scheme == "https" and parsed.netloc:
            return redirect(target, code=302)
    return jsonify({"status": "referral_tracked", "agent_id": row.agent_id, "slug": row.slug, "next_step": "create_customer_or_quote"})


@bp.post("/referral-attribution")
def referral_attribution():
    data = request.get_json(silent=True) or {}
    row = db.session.execute(select(AgentReferralLink).filter_by(slug=data.get("slug"), is_active=True)).scalar_one_or_none()
    if not row:
        return jsonify({"error": "referral_not_found"}), 404
    customer_id = data.get("customer_id")
    if not customer_id and data.get("customer_name"):
        c = Customer(name=data["customer_name"], mobile=data.get("customer_mobile"), email=data.get("customer_email"), source="agent_referral")
        db.session.add(c); db.session.flush(); customer_id = c.id
    lead_id = data.get("lead_id")
    if not lead_id and customer_id:
        lead = Lead(customer_id=customer_id, agent_id=row.agent_id, stage="new", product=data.get("product"), source="agent_referral")
        db.session.add(lead); db.session.flush(); lead_id = lead.id
    attr = ReferralAttribution(referral_link_id=row.id, customer_id=customer_id, lead_id=lead_id, external_reference=data.get("external_reference"), attribution_status=data.get("attribution_status", "tracked"))
    row.leads += 1
    db.session.add(attr); audit("agent.referral.attribution", "referral_attribution", attr.id); db.session.commit()
    return jsonify({"tracked": True, "agent_id": row.agent_id, "customer_id": customer_id, "lead_id": lead_id, "attribution_status": attr.attribution_status}), 201
