#!/usr/bin/env python3
"""P20 deterministic one-shot WhatsApp smoke test."""
from __future__ import annotations

import json
import os

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "p20-test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "p20-test-jwt-secret-012345678901234567890123")
os.environ.setdefault("DATABASE_URL", "sqlite:///p20_smoke.db")
os.environ.pop("WHATSAPP_WEBHOOK_SECRET", None)

import p0_runtime
from foundation.db import db
from foundation.p20_routes import _parse, _missing

app = p0_runtime.app
rules = {r.rule for r in app.url_map.iter_rules()}
assert "/api/p20/whatsapp/inbound" in rules
assert "/api/p20/whatsapp/intents" in rules
assert "/api/p20/whatsapp/health" in rules

parsed = _parse(
    "Need renewal for MH15AB1234, customer name: Prashant Chandratre, email prashant@example.com, comprehensive zero dep, engine protect",
    {"rc_attached": True, "policy_attached": True},
    "919999999999",
)
assert parsed["vehicle_number"] == "MH15AB1234"
assert parsed["email"] == "prashant@example.com"
assert parsed["policy_type"] == "comprehensive_zero_dep"
assert not _missing(parsed)

with app.app_context():
    db.create_all()
    client = app.test_client()
    response = client.post(
        "/api/p20/whatsapp/inbound",
        json={
            "id": "p20-smoke-001",
            "from": "919999999999",
            "text": "Need renewal for MH15AB1234, customer name: Prashant Chandratre, email prashant@example.com, comprehensive zero dep",
            "rc_attached": True,
            "policy_attached": True,
        },
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    body = response.get_json()
    assert body["status"] == "ready_for_quote", body
    assert body["next_action"] == "prepare_quote", body

print("P20 one-shot WhatsApp smoke: PASS")
