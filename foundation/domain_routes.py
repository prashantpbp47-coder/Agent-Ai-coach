"""P1 authenticated domain APIs for PartnersHub AI.

These APIs persist the core CRM/insurance entities without removing or changing
legacy Priya AI routes. Legacy data can be imported idempotently by an ADMIN.
"""

import json
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog, Customer, FollowUp, Lead, Policy, Quote, Renewal, RM
from .security import current_user, require_permission, require_role

bp = Blueprint("p1_domains", __name__, url_prefix="/api/p1")


def now():
    return datetime.now(timezone.utc)


def audit(action, resource_type=None, resource_id=None):
    user = current_user()
    db.session.add(AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user.id if user else None,
        request_id=str(uuid.uuid4()),
        ip_address=request.remote_addr,
    ))


def as_dict(obj, fields):
    return {field: getattr(obj, field) for field in fields}


def parse_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


AGENT_FIELDS = ["id", "partner_code", "name", "phone", "email", "city", "status", "rm_id"]
CUSTOMER_FIELDS = ["id", "name", "mobile", "email", "city", "source", "status"]
LEAD_FIELDS = ["id", "customer_id", "agent_id", "stage", "product", "source", "next_action_at", "notes"]
QUOTE_FIELDS = ["id", "lead_id", "insurer", "policy_type", "premium", "status", "external_reference", "payload_json"]
POLICY_FIELDS = ["id", "customer_id", "agent_id", "policy_number", "insurer", "product", "start_date", "expiry_date", "premium", "status"]
RENEWAL_FIELDS = ["id", "policy_id", "due_at", "stage", "last_contacted_at", "next_follow_up_at"]
FOLLOWUP_FIELDS = ["id", "lead_id", "renewal_id", "channel", "scheduled_at", "completed_at", "status", "attempt", "notes"]


def serialize(obj, fields):
    result = {}
    for field in fields:
        value = getattr(obj, field)
        result[field] = value.isoformat() if isinstance(value, datetime) else value
    return result


def dt(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def crud_list(model, fields, permission):
    @bp.get(f"/{model.__tablename__}")
    @require_permission(permission)
    def handler(model=model, fields=fields):
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
        rows = db.session.execute(select(model).offset(offset).limit(limit)).scalars().all()
        return jsonify({"items": [serialize(row, fields) for row in rows], "limit": limit, "offset": offset})


def create_agent():
    data = parse_json()
    required = ["partner_code", "name"]
    if any(not str(data.get(k, "")).strip() for k in required):
        return jsonify({"error": "partner_code_and_name_required"}), 400
    if db.session.execute(select(Agent).filter_by(partner_code=data["partner_code"])).scalar_one_or_none():
        return jsonify({"error": "partner_code_exists"}), 409
    obj = Agent(partner_code=data["partner_code"].strip(), name=data["name"].strip(), phone=data.get("phone"), email=data.get("email"), city=data.get("city"), status=data.get("status", "active"), rm_id=data.get("rm_id"))
    db.session.add(obj); db.session.flush(); audit("agent.create", "agent", obj.id); db.session.commit()
    return jsonify(serialize(obj, AGENT_FIELDS)), 201


@bp.post("/agents")
@require_permission("agents:write")
def agents_create():
    return create_agent()

crud_list(Agent, AGENT_FIELDS, "agents:read")


@bp.post("/rms")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def rms_create():
    data = parse_json()
    if not data.get("rm_code") or not data.get("name"):
        return jsonify({"error": "rm_code_and_name_required"}), 400
    if db.session.execute(select(RM).filter_by(rm_code=data["rm_code"])).scalar_one_or_none():
        return jsonify({"error": "rm_code_exists"}), 409
    obj = RM(rm_code=data["rm_code"], name=data["name"], phone=data.get("phone"), email=data.get("email"), status=data.get("status", "active"))
    db.session.add(obj); db.session.flush(); audit("rm.create", "rm", obj.id); db.session.commit()
    return jsonify(as_dict(obj, ["id", "rm_code", "name", "phone", "email", "status"])), 201

crud_list(RM, ["id", "rm_code", "name", "phone", "email", "status"], "agents:read")


@bp.post("/customers")
@require_permission("customers:write")
def customers_create():
    data = parse_json()
    if not data.get("name"):
        return jsonify({"error": "name_required"}), 400
    obj = Customer(name=data["name"].strip(), mobile=data.get("mobile"), email=data.get("email"), city=data.get("city"), source=data.get("source"), status=data.get("status", "active"))
    db.session.add(obj); db.session.flush(); audit("customer.create", "customer", obj.id); db.session.commit()
    return jsonify(serialize(obj, CUSTOMER_FIELDS)), 201

crud_list(Customer, CUSTOMER_FIELDS, "customers:read")


@bp.post("/leads")
@require_permission("leads:write")
def leads_create():
    data = parse_json()
    if not data.get("customer_id") and not data.get("customer"):
        return jsonify({"error": "customer_id_or_customer_required"}), 400
    customer_id = data.get("customer_id")
    if not customer_id:
        c = Customer(name=str(data["customer"]), mobile=data.get("mobile"), source=data.get("source", "legacy"))
        db.session.add(c); db.session.flush(); customer_id = c.id
    obj = Lead(customer_id=customer_id, agent_id=data.get("agent_id"), stage=data.get("stage", "new"), product=data.get("product"), source=data.get("source"), next_action_at=dt(data.get("next_action_at")), notes=data.get("notes"))
    db.session.add(obj); db.session.flush(); audit("lead.create", "lead", obj.id); db.session.commit()
    return jsonify(serialize(obj, LEAD_FIELDS)), 201

crud_list(Lead, LEAD_FIELDS, "leads:read")


@bp.post("/quotes")
@require_permission("quotes:write")
def quotes_create():
    data = parse_json()
    if not data.get("lead_id") and not data.get("customer_id"):
        return jsonify({"error": "lead_id_or_customer_id_required"}), 400
    lead_id = data.get("lead_id")
    if not lead_id:
        c_id = data["customer_id"]
        lead = Lead(customer_id=c_id, agent_id=data.get("agent_id"), stage="quoted", product=data.get("product", "motor"), source="p1_quote")
        db.session.add(lead); db.session.flush(); lead_id = lead.id
    obj = Quote(lead_id=lead_id, insurer=data.get("insurer"), policy_type=data.get("policy_type"), premium=data.get("premium"), status=data.get("status", "draft"), external_reference=data.get("external_reference"), payload_json=json.dumps(data.get("payload", {})))
    db.session.add(obj); db.session.flush(); audit("quote.create", "quote", obj.id); db.session.commit()
    return jsonify(serialize(obj, QUOTE_FIELDS)), 201

crud_list(Quote, QUOTE_FIELDS, "quotes:read")


@bp.post("/policies")
@require_permission("policies:write")
def policies_create():
    data = parse_json()
    if not data.get("customer_id"):
        return jsonify({"error": "customer_id_required"}), 400
    obj = Policy(customer_id=data["customer_id"], agent_id=data.get("agent_id"), policy_number=data.get("policy_number"), insurer=data.get("insurer"), product=data.get("product"), start_date=dt(data.get("start_date")), expiry_date=dt(data.get("expiry_date")), premium=data.get("premium"), status=data.get("status", "active"))
    db.session.add(obj); db.session.flush(); audit("policy.create", "policy", obj.id); db.session.commit()
    return jsonify(serialize(obj, POLICY_FIELDS)), 201

crud_list(Policy, POLICY_FIELDS, "policies:read")


@bp.post("/renewals")
@require_permission("renewals:write")
def renewals_create():
    data = parse_json()
    if not data.get("policy_id"):
        return jsonify({"error": "policy_id_required"}), 400
    obj = Renewal(policy_id=data["policy_id"], due_at=dt(data.get("due_at")), stage=data.get("stage", "pending"), last_contacted_at=dt(data.get("last_contacted_at")), next_follow_up_at=dt(data.get("next_follow_up_at")))
    db.session.add(obj); db.session.flush(); audit("renewal.create", "renewal", obj.id); db.session.commit()
    return jsonify(serialize(obj, RENEWAL_FIELDS)), 201

crud_list(Renewal, RENEWAL_FIELDS, "renewals:read")


@bp.post("/follow-ups")
@require_permission("leads:write")
def followups_create():
    data = parse_json()
    if not data.get("channel") or not data.get("scheduled_at"):
        return jsonify({"error": "channel_and_scheduled_at_required"}), 400
    obj = FollowUp(lead_id=data.get("lead_id"), renewal_id=data.get("renewal_id"), channel=data["channel"], scheduled_at=dt(data["scheduled_at"]), status=data.get("status", "pending"), attempt=int(data.get("attempt", 1)), notes=data.get("notes"))
    db.session.add(obj); db.session.flush(); audit("follow_up.create", "follow_up", obj.id); db.session.commit()
    return jsonify(serialize(obj, FOLLOWUP_FIELDS)), 201

crud_list(FollowUp, FOLLOWUP_FIELDS, "leads:read")


@bp.post("/legacy/import")
@require_role("ADMIN")
def import_legacy():
    """Idempotently copy the existing in-memory AGENTS list into persistent Agent rows."""
    from app import AGENTS
    created = 0
    updated = 0
    for item in AGENTS:
        obj = db.session.execute(select(Agent).filter_by(partner_code=item["agent_id"])).scalar_one_or_none()
        if not obj:
            obj = Agent(partner_code=item["agent_id"], name=item["name"], phone=item.get("phone"), status="active")
            db.session.add(obj); created += 1
        else:
            obj.name = item["name"]; obj.phone = item.get("phone"); updated += 1
    audit("legacy.import_agents", "agent", None)
    db.session.commit()
    return jsonify({"created": created, "updated": updated, "source_count": len(AGENTS)})


@bp.get("/summary")
@require_permission("reports:read")
def summary():
    return jsonify({
        "agents": db.session.scalar(select(db.func.count()).select_from(Agent)),
        "customers": db.session.scalar(select(db.func.count()).select_from(Customer)),
        "leads": db.session.scalar(select(db.func.count()).select_from(Lead)),
        "quotes": db.session.scalar(select(db.func.count()).select_from(Quote)),
        "policies": db.session.scalar(select(db.func.count()).select_from(Policy)),
        "renewals": db.session.scalar(select(db.func.count()).select_from(Renewal)),
        "follow_ups": db.session.scalar(select(db.func.count()).select_from(FollowUp)),
    })
