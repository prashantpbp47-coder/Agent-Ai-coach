"""P6 persistent WhatsApp-style inbox and lead capture APIs.

This layer is provider-neutral: Interakt/Twilio webhooks can feed the same
endpoint later. It intentionally stores inbound messages and documents without
claiming OCR/provider completion that has not occurred.
"""
import json, uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import select
from .db import db
from .models import Agent, Customer, Lead, AuditLog
from .models_p6 import InboxThread, InboxMessage, CustomerDocument, AgentLeadMessage
from .security import current_user, require_permission, require_role

bp = Blueprint("p6", __name__, url_prefix="/api/p6")

def now():
    return datetime.now(timezone.utc)

def audit(action, resource_type, resource_id=None):
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=resource_type,
        resource_id=resource_id, user_id=u.id if u else None,
        request_id=str(uuid.uuid4()), ip_address=request.remote_addr))

def normalize_phone(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits

def intent_from_text(text):
    t = str(text or "").lower()
    if any(x in t for x in ("quote", "quotation", "premium", "policy price")): return "quote_request"
    if any(x in t for x in ("renew", "renewal", "expiry")): return "renewal"
    if any(x in t for x in ("rc", "registration", "vehicle")): return "document_intake"
    if any(x in t for x in ("claim", "accident")): return "claim"
    return "general"

def resolve_agent(agent_id=None, partner_code=None):
    if agent_id: return db.session.get(Agent, agent_id)
    if partner_code: return db.session.execute(select(Agent).filter_by(partner_code=partner_code)).scalar_one_or_none()
    return None

@bp.post("/inbound")
def inbound():
    """Provider-neutral inbound message receiver. Provider signature validation belongs at the edge adapter."""
    data = request.get_json(silent=True) or {}
    sender = normalize_phone(data.get("sender"))
    if not sender:
        return jsonify({"error": "sender_required"}), 400
    external_id = data.get("external_message_id")
    if external_id:
        dup = db.session.execute(select(InboxMessage).filter_by(external_message_id=external_id)).scalar_one_or_none()
        if dup:
            return jsonify({"duplicate": True, "message_id": dup.id}), 200
    agent = resolve_agent(data.get("agent_id"), data.get("partner_code"))
    customer = db.session.execute(select(Customer).where(Customer.mobile.like(f"%{sender}"))).scalars().first()
    if not customer:
        customer = Customer(name=str(data.get("customer_name") or "WhatsApp Customer").strip(), mobile=sender, source="whatsapp")
        db.session.add(customer); db.session.flush()
    thread_key = str(data.get("external_thread_id") or f"wa:{sender}:{agent.id if agent else 'unassigned'}")
    thread = db.session.execute(select(InboxThread).filter_by(external_thread_id=thread_key)).scalar_one_or_none()
    if not thread:
        thread = InboxThread(agent_id=agent.id if agent else None, customer_id=customer.id, channel="whatsapp", external_thread_id=thread_key)
        db.session.add(thread); db.session.flush()
    text = str(data.get("text") or "")
    msg = InboxMessage(thread_id=thread.id, direction="inbound", sender=sender, message_type=data.get("message_type", "text"), text=text, media_url=data.get("media_url"), external_message_id=external_id)
    db.session.add(msg)
    thread.last_message_at = now()
    intent = intent_from_text(text)
    lead = db.session.execute(select(Lead).where(Lead.customer_id == customer.id, Lead.agent_id == (agent.id if agent else None), Lead.stage.not_in(["closed","lost"])).order_by(Lead.created_at.desc())).scalars().first()
    if not lead:
        lead = Lead(customer_id=customer.id, agent_id=agent.id if agent else None, stage="new", product="motor" if intent in ("quote_request","document_intake") else None, source="whatsapp")
        db.session.add(lead); db.session.flush()
    alm = AgentLeadMessage(agent_id=agent.id if agent else None, customer_id=customer.id, lead_id=lead.id, channel="whatsapp", intent=intent, message_text=text, status="new") if agent else None
    if alm: db.session.add(alm)
    audit("p6.inbound_message", "inbox_message", msg.id)
    db.session.commit()
    return jsonify({"received": True, "message_id": msg.id, "thread_id": thread.id, "customer_id": customer.id, "lead_id": lead.id, "agent_id": agent.id if agent else None, "intent": intent}), 201

@bp.get("/inbox")
@require_permission("leads:read")
def inbox():
    agent_id = request.args.get("agent_id")
    q = select(InboxThread)
    if agent_id: q = q.where(InboxThread.agent_id == agent_id)
    rows = db.session.execute(q.order_by(InboxThread.last_message_at.desc()).limit(100)).scalars().all()
    return jsonify({"items": [{"thread_id": t.id, "agent_id": t.agent_id, "customer_id": t.customer_id, "channel": t.channel, "status": t.status, "last_message_at": t.last_message_at.isoformat()} for t in rows]})

@bp.get("/threads/<thread_id>")
@require_permission("leads:read")
def thread(thread_id):
    t = db.session.get(InboxThread, thread_id)
    if not t: return jsonify({"error": "thread_not_found"}), 404
    msgs = db.session.execute(select(InboxMessage).where(InboxMessage.thread_id == thread_id).order_by(InboxMessage.created_at)).scalars().all()
    return jsonify({"thread": {"id": t.id, "agent_id": t.agent_id, "customer_id": t.customer_id, "status": t.status}, "messages": [{"id": m.id, "direction": m.direction, "sender": m.sender, "type": m.message_type, "text": m.text, "media_url": m.media_url, "created_at": m.created_at.isoformat()} for m in msgs]})

@bp.post("/documents")
@require_permission("customers:write")
def add_document():
    data = request.get_json(silent=True) or {}
    if not data.get("customer_id") or not data.get("document_type"):
        return jsonify({"error": "customer_id_and_document_type_required"}), 400
    if not db.session.get(Customer, data["customer_id"]): return jsonify({"error": "customer_not_found"}), 404
    doc = CustomerDocument(customer_id=data["customer_id"], lead_id=data.get("lead_id"), document_type=data["document_type"], storage_url=data.get("storage_url"), extracted_text=data.get("extracted_text"), extracted_json=json.dumps(data.get("extracted_json")) if data.get("extracted_json") is not None else None, ocr_status=data.get("ocr_status", "pending"), verified=bool(data.get("verified", False)))
    db.session.add(doc); db.session.flush(); audit("p6.document.add", "customer_document", doc.id); db.session.commit()
    return jsonify({"document_id": doc.id, "customer_id": doc.customer_id, "lead_id": doc.lead_id, "document_type": doc.document_type, "ocr_status": doc.ocr_status, "verified": doc.verified}), 201

@bp.post("/quote-prepare")
@require_permission("quotes:write")
def quote_prepare():
    data = request.get_json(silent=True) or {}
    if not data.get("customer_id"): return jsonify({"error": "customer_id_required"}), 400
    customer = db.session.get(Customer, data["customer_id"])
    if not customer: return jsonify({"error": "customer_not_found"}), 404
    agent = resolve_agent(data.get("agent_id"), data.get("partner_code"))
    if not agent: return jsonify({"error": "agent_required"}), 400
    lead = db.session.get(Lead, data.get("lead_id")) if data.get("lead_id") else None
    if not lead:
        lead = Lead(customer_id=customer.id, agent_id=agent.id, stage="qualified", product=data.get("product", "motor"), source="p6_quote_prepare", notes=data.get("notes")); db.session.add(lead); db.session.flush()
    required = ["vehicle_type", "policy_type", "year"]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing: return jsonify({"status":"needs_details", "missing":missing, "customer_id":customer.id, "lead_id":lead.id, "next":"collect_missing_fields_or_documents"}), 200
    from app import calc_quote
    try:
        quotation = calc_quote(data.get("vehicle_type"), data.get("policy_type"), data.get("year"), data.get("idv", 0), data.get("ncb_years", 0), bool(data.get("has_claim", False)))
    except (TypeError, ValueError) as exc:
        return jsonify({"error":"invalid_quote_input","detail":str(exc)}),400
    audit("p6.quote.prepare", "lead", lead.id); db.session.commit()
    return jsonify({"status":"ready_for_quote","customer_id":customer.id,"lead_id":lead.id,"agent_id":agent.id,"quotation":quotation,"note":"Use approved provider quote flow for authoritative premium and issuance."})

@bp.get("/agent/<agent_id>/summary")
@require_permission("leads:read")
def agent_summary(agent_id):
    agent = db.session.get(Agent, agent_id)
    if not agent: return jsonify({"error":"agent_not_found"}),404
    threads = db.session.execute(select(InboxThread).where(InboxThread.agent_id==agent_id)).scalars().all()
    return jsonify({"agent_id":agent_id,"partner_code":agent.partner_code,"open_threads":sum(t.status=="open" for t in threads),"total_threads":len(threads)})
