"""P2 bridge: persist the existing legacy quotation flow."""

import json
from datetime import datetime
import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog, Customer, Lead, Quote
from .security import current_user, require_permission

bp = Blueprint("p2_quote_bridge", __name__, url_prefix="/api/p2")


def audit(action, resource_type, resource_id=None):
    user = current_user()
    db.session.add(AuditLog(action=action, resource_type=resource_type, resource_id=resource_id,
                            user_id=user.id if user else None, request_id=str(uuid.uuid4()),
                            ip_address=request.remote_addr))


@bp.post("/quote-request")
@require_permission("quotes:write")
def persistent_quote_request():
    """Run the repository's existing calculator and persist Customer -> Lead -> Quote."""
    from app import calc_quote
    data = request.get_json(silent=True) or {}
    try:
        quotation = calc_quote(data.get("vehicle_type", "car"), data.get("policy_type", "comprehensive"),
                               data.get("year", datetime.now().year - 3), data.get("idv", 0),
                               data.get("ncb_years", 0), bool(data.get("has_claim", False)))
    except (TypeError, ValueError) as exc:
        return jsonify({"error": "invalid_quote_input", "detail": str(exc)}), 400

    agent = None
    agent_code = str(data.get("agent_id", "")).strip()
    if agent_code:
        agent = db.session.execute(select(Agent).filter_by(partner_code=agent_code)).scalar_one_or_none()
        if not agent:
            return jsonify({"error": "agent_not_found", "agent_id": agent_code}), 404

    mobile = str(data.get("customer_mobile", "")).strip() or None
    customer = db.session.execute(select(Customer).filter_by(mobile=mobile)).scalars().first() if mobile else None
    if not customer:
        customer = Customer(name=str(data.get("customer_name", "Unknown Customer")).strip() or "Unknown Customer",
                            mobile=mobile, email=data.get("customer_email"), source=data.get("source", "quote_request"))
        db.session.add(customer)
        db.session.flush()
    elif data.get("customer_name"):
        customer.name = str(data["customer_name"]).strip()

    lead = Lead(customer_id=customer.id, agent_id=agent.id if agent else None, stage="quoted",
                product="motor", source=data.get("source", "quote_request"), notes=data.get("notes"))
    db.session.add(lead)
    db.session.flush()

    quote = Quote(lead_id=lead.id, insurer=data.get("insurer"), policy_type=quotation.get("policy_type"),
                  premium=int(quotation.get("total", 0)), status="generated",
                  external_reference=data.get("external_reference"),
                  payload_json=json.dumps({"request": data, "quotation": quotation}, default=str))
    db.session.add(quote)
    db.session.flush()
    audit("quote.generate_persisted", "quote", quote.id)
    db.session.commit()

    return jsonify({"success": True, "quote_id": quote.id, "lead_id": lead.id,
                    "customer_id": customer.id, "agent": agent.name if agent else None,
                    "quotation": quotation, "persistent": True}), 201
