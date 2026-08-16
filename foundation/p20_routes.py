"""P20 WhatsApp one-shot quotation orchestrator.

The agent can send requirements in one message. The service extracts what is
present, stores the state, and returns one consolidated request for everything
still missing. It never forces a question-by-question chatbot sequence.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog
from .models_p20 import WhatsAppEvent, WhatsAppQuoteIntent, WhatsAppSession
from .security import current_user, require_auth, require_role

bp = Blueprint("p20_whatsapp", __name__, url_prefix="/api/p20")

VEHICLE_RE = re.compile(r"\b[A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{3,4}\b", re.I)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
DATE_RE = re.compile(r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b")


def now():
    return datetime.now(timezone.utc)


def _phone(value: str) -> str:
    return re.sub(r"[^0-9+]", "", str(value or ""))[-15:]


def _signature_ok(body: bytes) -> bool:
    secret = os.getenv("WHATSAPP_WEBHOOK_SECRET", "").strip()
    if not secret:
        return os.getenv("FLASK_ENV", "production") != "production"
    supplied = request.headers.get("X-PartnersHub-Signature", "")
    supplied = supplied.removeprefix("sha256=")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return bool(supplied) and hmac.compare_digest(supplied, expected)


def _text(payload: dict) -> str:
    for key in ("text", "body", "message", "caption"):
        if payload.get(key):
            return str(payload[key]).strip()
    message = payload.get("message")
    if isinstance(message, dict):
        for key in ("text", "body", "caption"):
            if message.get(key):
                return str(message[key]).strip()
    return ""


def _media(payload: dict) -> tuple[bool, bool]:
    files = payload.get("files") or payload.get("media") or []
    if isinstance(files, dict): files = [files]
    names = " ".join(str(x).lower() for x in files)
    rc = bool(payload.get("rc_attached") or "rc" in names or "registration" in names)
    policy = bool(payload.get("policy_attached") or "policy" in names or "insurance" in names)
    return rc, policy


def _parse(text: str, payload: dict, phone: str) -> dict:
    lower = text.lower()
    vehicle = VEHICLE_RE.search(text)
    email = EMAIL_RE.search(text)
    policy_type = None
    if any(x in lower for x in ("zero dep", "zero depreciation", "zerodep")):
        policy_type = "comprehensive_zero_dep"
    elif any(x in lower for x in ("comprehensive", "package")):
        policy_type = "comprehensive"
    elif any(x in lower for x in ("third party", "third-party", "3rd party", "tp")):
        policy_type = "third_party"

    add_ons = []
    for label, keys in {
        "zero_dep": ("zero dep", "zero depreciation"),
        "engine_protect": ("engine protect",),
        "roadside_assistance": ("roadside", "rsa"),
        "return_to_invoice": ("return to invoice", "rti"),
        "consumables": ("consumables",),
        "key_protect": ("key protect",),
    }.items():
        if any(k in lower for k in keys): add_ons.append(label)

    name = None
    m = re.search(r"(?:name|customer)\s*[:=-]\s*([A-Za-z][A-Za-z .'-]{2,80})", text, re.I)
    if m: name = m.group(1).strip()

    expiry = None
    m = re.search(r"(?:expiry|expires|renewal|policy expiry)\s*[:=-]?\s*(" + DATE_RE.pattern[2:-2] + r")", text, re.I)
    if m: expiry = m.group(1)
    elif any(x in lower for x in ("expiry", "renewal")) and DATE_RE.search(text): expiry = DATE_RE.search(text).group(0)

    rc, policy = _media(payload)
    return {
        "phone": phone,
        "vehicle_number": vehicle.group(0).upper().replace(" ", "").replace("-", "") if vehicle else None,
        "customer_name": name,
        "email": email.group(0).lower() if email else None,
        "policy_type": policy_type,
        "add_ons": add_ons,
        "expiry_date": expiry,
        "rc_attached": rc,
        "policy_attached": policy,
    }


def _merge(existing: dict, incoming: dict) -> dict:
    result = dict(existing or {})
    for key, value in incoming.items():
        if value not in (None, "", [], False): result[key] = value
    for key in ("add_ons",):
        if incoming.get(key): result[key] = sorted(set((existing.get(key) or []) + incoming[key]))
    result["phone"] = incoming.get("phone") or result.get("phone")
    return result


def _missing(data: dict) -> list[str]:
    missing = []
    if not data.get("vehicle_number"): missing.append("vehicle number / RC")
    if not data.get("policy_type"): missing.append("plan preference (Comprehensive / Comprehensive + Zero Dep / Third Party)")
    if not data.get("rc_attached"): missing.append("RC copy")
    if not data.get("policy_attached"): missing.append("previous/current policy copy")
    if not data.get("customer_name"): missing.append("customer name")
    if not data.get("email"): missing.append("email ID")
    return missing


def _reply(data: dict, missing: list[str]) -> str:
    if not missing:
        return ("Perfect. I have captured all requirements in one go. "
                f"Vehicle: {data['vehicle_number']}. Plan: {data['policy_type']}. "
                "Your request is now ready for quotation processing. I will use the uploaded RC/policy details for validation before presenting the final premium.")
    joined = "\n".join(f"• {item}" for item in missing)
    return ("Got it — I have captured everything you sent, so no need to answer questions one by one. "
            "Please send the following remaining items together in one message/upload:\n" + joined +
            "\n\nOnce received, the request will move directly to quotation preparation.")


@bp.post("/whatsapp/inbound")
def inbound():
    raw = request.get_data(cache=True)
    if not _signature_ok(raw): return jsonify({"error": "invalid_webhook_signature"}), 401
    payload = request.get_json(silent=True) or {}
    phone = _phone(payload.get("from") or payload.get("phone") or payload.get("wa_id"))
    event_id = str(payload.get("message_id") or payload.get("id") or hashlib.sha256(raw).hexdigest())
    text = _text(payload)
    if not phone or not text:
        return jsonify({"error": "phone_and_message_required"}), 400
    duplicate = db.session.execute(select(WhatsAppEvent).where(WhatsAppEvent.external_message_id == event_id)).scalar_one_or_none()
    if duplicate:
        intent = db.session.execute(select(WhatsAppQuoteIntent).where(WhatsAppQuoteIntent.phone == phone).order_by(WhatsAppQuoteIntent.created_at.desc()).limit(1)).scalar_one_or_none()
        return jsonify({"duplicate": True, "intent_id": intent.id if intent else None})

    event = WhatsAppEvent(external_message_id=event_id, phone=phone, direction="inbound", body=text, payload_json=json.dumps(payload, ensure_ascii=False))
    db.session.add(event)
    session = db.session.execute(select(WhatsAppSession).where(WhatsAppSession.phone == phone)).scalar_one_or_none()
    if not session:
        session = WhatsAppSession(phone=phone, state="collecting", collected_json="{}")
        db.session.add(session); db.session.flush()
    previous = json.loads(session.collected_json or "{}")
    parsed = _parse(text, payload, phone)
    merged = _merge(previous, parsed)
    missing = _missing(merged)
    status = "ready_for_quote" if not missing else "collecting"
    session.collected_json = json.dumps(merged, ensure_ascii=False)
    session.state = status
    session.last_message_at = now()
    intent = db.session.execute(select(WhatsAppQuoteIntent).where(WhatsAppQuoteIntent.session_id == session.id, WhatsAppQuoteIntent.status.in_(["collecting", "ready_for_quote"])).order_by(WhatsAppQuoteIntent.created_at.desc()).limit(1)).scalar_one_or_none()
    if not intent:
        intent = WhatsAppQuoteIntent(session_id=session.id, phone=phone, raw_text=text)
        db.session.add(intent)
    intent.status = status
    intent.vehicle_number = merged.get("vehicle_number")
    intent.customer_name = merged.get("customer_name")
    intent.email = merged.get("email")
    intent.policy_type = merged.get("policy_type")
    intent.add_ons = json.dumps(merged.get("add_ons") or [])
    intent.expiry_date = merged.get("expiry_date")
    intent.rc_attached = bool(merged.get("rc_attached"))
    intent.policy_attached = bool(merged.get("policy_attached"))
    intent.normalized_json = json.dumps(merged, ensure_ascii=False)
    intent.raw_text = text
    db.session.commit()
    return jsonify({"ok": True, "intent_id": intent.id, "status": status, "missing_fields": missing, "normalized": merged, "reply": _reply(merged, missing), "next_action": "prepare_quote" if not missing else "collect_all_missing_items_once"})


@bp.get("/whatsapp/intents")
@require_auth
@require_role("RM", "MASTER_AGENT", "ADMIN")
def intents():
    rows = db.session.execute(select(WhatsAppQuoteIntent).order_by(WhatsAppQuoteIntent.updated_at.desc()).limit(min(int(request.args.get("limit", 50)), 200))).scalars().all()
    return jsonify({"count": len(rows), "items": [{"id": x.id, "phone": x.phone, "status": x.status, "vehicle_number": x.vehicle_number, "customer_name": x.customer_name, "email": x.email, "policy_type": x.policy_type, "rc_attached": x.rc_attached, "policy_attached": x.policy_attached, "created_at": x.created_at.isoformat(), "updated_at": x.updated_at.isoformat()} for x in rows]})


@bp.get("/whatsapp/health")
def health():
    return jsonify({"module": "p20_whatsapp_one_shot", "webhook_secret_configured": bool(os.getenv("WHATSAPP_WEBHOOK_SECRET")), "mode": "single-message-requirements"})
