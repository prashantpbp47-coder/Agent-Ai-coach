"""P3 provider API: normalized insurer/PBPartners integration boundary."""

import json
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import AuditLog, Quote
from .providers import available_providers, provider
from .security import current_user, require_permission

bp = Blueprint("p3_providers", __name__, url_prefix="/api/p3/providers")


def audit(action, resource_type=None, resource_id=None, metadata=None):
    user = current_user()
    db.session.add(AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user.id if user else None,
        request_id=str(uuid.uuid4()),
        ip_address=request.remote_addr,
        metadata_json=json.dumps(metadata or {}, default=str),
    ))


@bp.get("")
@require_permission("quotes:read")
def list_providers():
    return jsonify({"providers": available_providers()})


@bp.post("/quote")
@require_permission("quotes:write")
def provider_quote():
    data = request.get_json(silent=True) or {}
    name = str(data.get("provider", "pbpartners")).lower().strip()
    adapter = provider(name)
    if not adapter:
        return jsonify({"error": "provider_not_supported", "provider": name}), 404

    result = adapter.quote(data)
    quote_id = data.get("quote_id")
    quote = db.session.execute(select(Quote).where(Quote.id == quote_id)).scalar_one_or_none() if quote_id else None
    if quote:
        quote.insurer = name
        quote.status = "provider_pending" if result.status == "not_configured" else result.status
        quote.external_reference = result.quote_reference
        existing = {}
        if quote.payload_json:
            try:
                existing = json.loads(quote.payload_json)
            except (TypeError, ValueError):
                existing = {}
        existing["provider_result"] = result.as_dict()
        quote.payload_json = json.dumps(existing, default=str)

    audit("provider.quote", "quote", quote_id, {"provider": name, "status": result.status, "error_code": result.error_code})
    db.session.commit()
    return jsonify({"success": result.status != "error", "result": result.as_dict()}), 200
