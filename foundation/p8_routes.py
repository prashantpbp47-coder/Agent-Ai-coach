"""P8 production-oriented message dispatch, status callbacks and opt-out APIs."""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta

import requests
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog
from .models_p7 import AgentDailyMessage
from .p8_models import MessageDelivery, MessagingConsent
from .security import current_user, require_role

bp = Blueprint("p8", __name__, url_prefix="/api/p8")


def now():
    return datetime.now(timezone.utc)


def audit(action, kind, rid=None):
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid,
                            user_id=u.id if u else None, request_id=str(uuid.uuid4()),
                            ip_address=request.remote_addr))


def normalize_phone(phone):
    value = str(phone or "").strip()
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) == 10:
        return "+91" + digits
    if value.startswith("+") and len(digits) >= 10:
        return "+" + digits
    return value


def opted_out(agent_id, channel):
    c = db.session.execute(select(MessagingConsent).filter_by(agent_id=agent_id)).scalar_one_or_none()
    if not c:
        return False
    return c.whatsapp_opt_out if channel.lower() == "whatsapp" else c.sms_opt_out


def send_interakt(phone, body):
    key = os.environ.get("INTERAKT_API_KEY") or os.environ.get("INTERAKT_KEY")
    if not key:
        return None, "provider_not_configured", "INTERAKT_API_KEY missing"
    try:
        r = requests.post(
            "https://api.interakt.ai/v1/public/message/",
            json={"fullPhoneNumber": phone, "callbackData": "partnershub_p8", "type": "Text", "data": {"message": body}},
            headers={"Authorization": f"Basic {key}", "Content-Type": "application/json"}, timeout=15)
        if r.status_code not in (200, 201, 202):
            return None, "provider_rejected", f"HTTP {r.status_code}: {r.text[:300]}"
        payload = r.json() if r.content else {}
        return payload.get("id") or payload.get("messageId") or payload.get("requestId"), None, None
    except requests.RequestException as exc:
        return None, "provider_unreachable", str(exc)


def send_twilio(phone, body):
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    sender = os.environ.get("TWILIO_FROM_NUMBER")
    if not all((sid, token, sender)):
        return None, "provider_not_configured", "Twilio credentials missing"
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body=body, from_=sender, to=phone,
            status_callback=os.environ.get("TWILIO_MESSAGE_STATUS_CALLBACK"))
        return msg.sid, None, None
    except Exception as exc:
        return None, "provider_error", str(exc)


def dispatch_one(row, provider="interakt"):
    agent = db.session.get(Agent, row.agent_id)
    if not agent or not agent.phone:
        row.status = "failed"; row.failed_at = now(); row.error_code = "agent_phone_missing"; row.error_message = "Agent or phone unavailable"
        return row, False
    if opted_out(agent.id, row.channel):
        row.status = "opted_out"; row.failed_at = now(); row.error_code = "opted_out"; row.error_message = "Messaging opt-out is active"
        return row, False
    phone = normalize_phone(agent.phone)
    ref = err_code = err_msg = None
    if provider == "twilio":
        ref, err_code, err_msg = send_twilio(phone, row.body)
    else:
        ref, err_code, err_msg = send_interakt(phone, row.body)
    row.provider_reference = ref
    if ref:
        row.status = "sent"; row.sent_at = now(); row.error_code = None; row.error_message = None
        row.attempt = max(row.attempt, 1)
        return row, True
    row.status = "failed"; row.failed_at = now(); row.error_code = err_code; row.error_message = err_msg
    if row.attempt < 3:
        row.next_retry_at = now() + timedelta(minutes=5 * row.attempt)
    return row, False


@bp.post("/dispatch")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def dispatch():
    data = request.get_json(silent=True) or {}
    provider = str(data.get("provider", "interakt")).lower()
    limit = min(max(int(data.get("limit", 50)), 1), 200)
    rows = db.session.execute(select(AgentDailyMessage).where(AgentDailyMessage.status == "queued").order_by(AgentDailyMessage.created_at).limit(limit)).scalars().all()
    results = []
    for row in rows:
        delivery = MessageDelivery(daily_message_id=row.id, agent_id=row.agent_id, provider=provider, status="queued", attempt=1)
        db.session.add(delivery); db.session.flush()
        _, ok = dispatch_one(delivery, provider)
        if ok:
            row.status = "sent"; row.sent_at = delivery.sent_at; row.provider_reference = delivery.provider_reference
        elif delivery.status == "opted_out":
            row.status = "opted_out"
        else:
            row.status = "failed"
        audit("agent.message.dispatch", "message_delivery", delivery.id)
        results.append({"message_id": row.id, "delivery_id": delivery.id, "agent_id": row.agent_id, "status": delivery.status, "provider_reference": delivery.provider_reference, "error_code": delivery.error_code})
    db.session.commit()
    return jsonify({"provider": provider, "processed": len(results), "results": results})


@bp.post("/consent/<agent_id>")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def consent(agent_id):
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"error": "agent_not_found"}), 404
    data = request.get_json(silent=True) or {}
    row = db.session.execute(select(MessagingConsent).filter_by(agent_id=agent_id)).scalar_one_or_none()
    if not row:
        row = MessagingConsent(agent_id=agent_id); db.session.add(row)
    if "whatsapp_opt_out" in data: row.whatsapp_opt_out = bool(data["whatsapp_opt_out"])
    if "sms_opt_out" in data: row.sms_opt_out = bool(data["sms_opt_out"])
    audit("messaging.consent.update", "messaging_consent", row.id); db.session.commit()
    return jsonify({"agent_id": agent_id, "whatsapp_opt_out": row.whatsapp_opt_out, "sms_opt_out": row.sms_opt_out})


@bp.post("/status/twilio")
def twilio_status_callback():
    data = request.form.to_dict() or (request.get_json(silent=True) or {})
    provider_ref = data.get("MessageSid") or data.get("SmsSid")
    status = str(data.get("MessageStatus") or data.get("SmsStatus") or "").lower()
    if not provider_ref:
        return jsonify({"accepted": False, "error": "MessageSid_required"}), 400
    row = db.session.execute(select(MessageDelivery).filter_by(provider="twilio", provider_reference=provider_ref)).scalar_one_or_none()
    if not row:
        return jsonify({"accepted": True, "matched": False}), 200
    row.callback_payload = json.dumps(data, default=str)
    row.status = status or row.status
    timestamp = now()
    if status == "sent": row.sent_at = row.sent_at or timestamp
    elif status == "delivered": row.delivered_at = timestamp
    elif status == "read": row.read_at = timestamp
    elif status in {"failed", "undelivered"}: row.failed_at = timestamp; row.error_code = str(data.get("ErrorCode") or "delivery_failed")
    db.session.commit()
    return jsonify({"accepted": True, "matched": True, "status": row.status}), 200


@bp.post("/retry")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def retry_failed():
    limit = min(max(int((request.get_json(silent=True) or {}).get("limit", 50)), 1), 200)
    rows = db.session.execute(select(MessageDelivery).where(MessageDelivery.status == "failed", MessageDelivery.attempt < 3).order_by(MessageDelivery.created_at).limit(limit)).scalars().all()
    results = []
    for row in rows:
        if row.next_retry_at and row.next_retry_at > now():
            continue
        row.attempt += 1
        _, ok = dispatch_one(row, row.provider)
        results.append({"delivery_id": row.id, "attempt": row.attempt, "status": row.status, "ok": ok})
    db.session.commit()
    return jsonify({"processed": len(results), "results": results})
