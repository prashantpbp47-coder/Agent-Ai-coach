"""P1 authenticated domain APIs for PartnersHub AI."""
import json
import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, AuditLog, Customer, FollowUp, Lead, Policy, Quote, Renewal, RM
from .security import current_user, require_permission, require_role

bp = Blueprint("p1_domains", __name__, url_prefix="/api/p1")

def audit(action, resource_type=None, resource_id=None):
    user = current_user()
    db.session.add(AuditLog(action=action, resource_type=resource_type, resource_id=resource_id, user_id=user.id if user else None, request_id=str(uuid.uuid4()), ip_address=request.remote_addr))

def dt(value):
    if not value: return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

def parse_json():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}

def serialize(obj, fields):
    out = {}
    for field in fields:
        value = getattr(obj, field)
        out[field] = value.isoformat() if isinstance(value, datetime) else value
    return out

def list_route(model, fields, permission, route):
    endpoint = f"p1_list_{model.__tablename__}"
    def handler():
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
        rows = db.session.execute(select(model).offset(offset).limit(limit)).scalars().all()
        return jsonify({"items": [serialize(row, fields) for row in rows], "limit": limit, "offset": offset})
    handler.__name__ = endpoint
    handler = require_permission(permission)(handler)
    bp.add_url_rule(route, endpoint=endpoint, view_func=handler, methods=["GET"])

AGENT_FIELDS=["id","partner_code","name","phone","email","city","status","rm_id"]
CUSTOMER_FIELDS=["id","name","mobile","email","city","source","status"]
LEAD_FIELDS=["id","customer_id","agent_id","stage","product","source","next_action_at","notes"]
QUOTE_FIELDS=["id","lead_id","insurer","policy_type","premium","status","external_reference","payload_json"]
POLICY_FIELDS=["id","customer_id","agent_id","policy_number","insurer","product","start_date","expiry_date","premium","status"]
RENEWAL_FIELDS=["id","policy_id","due_at","stage","last_contacted_at","next_follow_up_at"]
FOLLOWUP_FIELDS=["id","lead_id","renewal_id","channel","scheduled_at","completed_at","status","attempt","notes"]

@bp.post("/agents")
@require_permission("agents:write")
def create_agent():
    d=parse_json()
    if not d.get("partner_code") or not d.get("name"): return jsonify({"error":"partner_code_and_name_required"}),400
    if db.session.execute(select(Agent).filter_by(partner_code=d["partner_code"])).scalar_one_or_none(): return jsonify({"error":"partner_code_exists"}),409
    o=Agent(partner_code=d["partner_code"],name=d["name"],phone=d.get("phone"),email=d.get("email"),city=d.get("city"),status=d.get("status","active"),rm_id=d.get("rm_id")); db.session.add(o); db.session.flush(); audit("agent.create","agent",o.id); db.session.commit(); return jsonify(serialize(o,AGENT_FIELDS)),201

@bp.post("/rms")
@require_role("RM","MASTER_AGENT","ADMIN")
def create_rm():
    d=parse_json()
    if not d.get("rm_code") or not d.get("name"): return jsonify({"error":"rm_code_and_name_required"}),400
    if db.session.execute(select(RM).filter_by(rm_code=d["rm_code"])).scalar_one_or_none(): return jsonify({"error":"rm_code_exists"}),409
    o=RM(rm_code=d["rm_code"],name=d["name"],phone=d.get("phone"),email=d.get("email"),status=d.get("status","active")); db.session.add(o); db.session.flush(); audit("rm.create","rm",o.id); db.session.commit(); return jsonify(serialize(o,["id","rm_code","name","phone","email","status"])),201

@bp.post("/customers")
@require_permission("customers:write")
def create_customer():
    d=parse_json()
    if not d.get("name"): return jsonify({"error":"name_required"}),400
    o=Customer(name=d["name"],mobile=d.get("mobile"),email=d.get("email"),city=d.get("city"),source=d.get("source"),status=d.get("status","active")); db.session.add(o); db.session.flush(); audit("customer.create","customer",o.id); db.session.commit(); return jsonify(serialize(o,CUSTOMER_FIELDS)),201

@bp.post("/leads")
@require_permission("leads:write")
def create_lead():
    d=parse_json(); cid=d.get("customer_id")
    if not cid and d.get("customer"):
        c=Customer(name=str(d["customer"]),mobile=d.get("mobile"),source=d.get("source","legacy")); db.session.add(c); db.session.flush(); cid=c.id
    if not cid: return jsonify({"error":"customer_id_or_customer_required"}),400
    o=Lead(customer_id=cid,agent_id=d.get("agent_id"),stage=d.get("stage","new"),product=d.get("product"),source=d.get("source"),next_action_at=dt(d.get("next_action_at")),notes=d.get("notes")); db.session.add(o); db.session.flush(); audit("lead.create","lead",o.id); db.session.commit(); return jsonify(serialize(o,LEAD_FIELDS)),201

@bp.post("/quotes")
@require_permission("quotes:write")
def create_quote():
    d=parse_json(); lid=d.get("lead_id")
    if not lid and d.get("customer_id"):
        lead=Lead(customer_id=d["customer_id"],agent_id=d.get("agent_id"),stage="quoted",product=d.get("product","motor"),source="p1_quote"); db.session.add(lead); db.session.flush(); lid=lead.id
    if not lid: return jsonify({"error":"lead_id_or_customer_id_required"}),400
    o=Quote(lead_id=lid,insurer=d.get("insurer"),policy_type=d.get("policy_type"),premium=d.get("premium"),status=d.get("status","draft"),external_reference=d.get("external_reference"),payload_json=json.dumps(d.get("payload",{}))); db.session.add(o); db.session.flush(); audit("quote.create","quote",o.id); db.session.commit(); return jsonify(serialize(o,QUOTE_FIELDS)),201

@bp.post("/policies")
@require_permission("policies:write")
def create_policy():
    d=parse_json()
    if not d.get("customer_id"): return jsonify({"error":"customer_id_required"}),400
    o=Policy(customer_id=d["customer_id"],agent_id=d.get("agent_id"),policy_number=d.get("policy_number"),insurer=d.get("insurer"),product=d.get("product"),start_date=dt(d.get("start_date")),expiry_date=dt(d.get("expiry_date")),premium=d.get("premium"),status=d.get("status","active")); db.session.add(o); db.session.flush(); audit("policy.create","policy",o.id); db.session.commit(); return jsonify(serialize(o,POLICY_FIELDS)),201

@bp.post("/renewals")
@require_permission("renewals:write")
def create_renewal():
    d=parse_json()
    if not d.get("policy_id"): return jsonify({"error":"policy_id_required"}),400
    o=Renewal(policy_id=d["policy_id"],due_at=dt(d.get("due_at")),stage=d.get("stage","pending"),last_contacted_at=dt(d.get("last_contacted_at")),next_follow_up_at=dt(d.get("next_follow_up_at"))); db.session.add(o); db.session.flush(); audit("renewal.create","renewal",o.id); db.session.commit(); return jsonify(serialize(o,RENEWAL_FIELDS)),201

@bp.post("/follow-ups")
@require_permission("leads:write")
def create_followup():
    d=parse_json()
    if not d.get("channel") or not d.get("scheduled_at"): return jsonify({"error":"channel_and_scheduled_at_required"}),400
    o=FollowUp(lead_id=d.get("lead_id"),renewal_id=d.get("renewal_id"),channel=d["channel"],scheduled_at=dt(d["scheduled_at"]),status=d.get("status","pending"),attempt=int(d.get("attempt",1)),notes=d.get("notes")); db.session.add(o); db.session.flush(); audit("follow_up.create","follow_up",o.id); db.session.commit(); return jsonify(serialize(o,FOLLOWUP_FIELDS)),201

@bp.post("/legacy/import")
@require_role("ADMIN")
def import_legacy():
    from app import AGENTS
    created=updated=0
    for item in AGENTS:
        o=db.session.execute(select(Agent).filter_by(partner_code=item["agent_id"])).scalar_one_or_none()
        if not o: o=Agent(partner_code=item["agent_id"],name=item["name"],phone=item.get("phone"),status="active"); db.session.add(o); created+=1
        else: o.name=item["name"]; o.phone=item.get("phone"); updated+=1
    audit("legacy.import_agents","agent"); db.session.commit(); return jsonify({"created":created,"updated":updated,"source_count":len(AGENTS)})

@bp.get("/summary")
@require_permission("reports:read")
def summary():
    def count(model): return db.session.scalar(select(func.count()).select_from(model)) or 0
    return jsonify({"agents":count(Agent),"rms":count(RM),"customers":count(Customer),"leads":count(Lead),"quotes":count(Quote),"policies":count(Policy),"renewals":count(Renewal),"follow_ups":count(FollowUp)})

list_route(Agent,AGENT_FIELDS,"agents:read","/agents")
list_route(RM,["id","rm_code","name","phone","email","status"],"agents:read","/rms")
list_route(Customer,CUSTOMER_FIELDS,"customers:read","/customers")
list_route(Lead,LEAD_FIELDS,"leads:read","/leads")
list_route(Quote,QUOTE_FIELDS,"quotes:read","/quotes")
list_route(Policy,POLICY_FIELDS,"policies:read","/policies")
list_route(Renewal,RENEWAL_FIELDS,"renewals:read","/renewals")
list_route(FollowUp,FOLLOWUP_FIELDS,"leads:read","/follow-ups")
