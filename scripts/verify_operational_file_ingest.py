#!/usr/bin/env python3
"""Deterministic P13 CSV operational-file ingestion smoke test."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "p13-test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "p13-test-jwt-secret-012345678901234567890123")
os.environ.setdefault("DATABASE_URL", "sqlite:///partnershub_p13_ingest.db")

import p0_runtime
from foundation.db import db
from foundation.models import Role, User
from foundation.security import hash_password, issue_token
from foundation.models_p13 import OperationalDataRecord

app = p0_runtime.app
rules = {rule.rule for rule in app.url_map.iter_rules()}
assert "/api/p13/operational/import-file" in rules
assert "/api/p13/operational/import-policy" in rules

with app.app_context():
    db.create_all()

    role = db.session.execute(
        db.select(Role).filter_by(name="ADMIN")
    ).scalar_one_or_none()
    if role is None:
        role = Role(name="ADMIN", description="Smoke-test administrator")
        db.session.add(role)
        db.session.flush()

    user = db.session.execute(
        db.select(User).filter_by(email="p13-smoke@example.com")
    ).scalar_one_or_none()
    if not user:
        user = User(
            email="p13-smoke@example.com",
            password_hash=hash_password("smoke-password"),
            full_name="P13 Smoke Administrator",
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

    if role not in user.roles:
        user.roles.append(role)
    db.session.commit()
    token = issue_token(user)

csv_data = (
    "IP Code,Partner Name,RM Code,Customer Name,Customer Mobile No.,Product,Insurer Name,Policy No.,Registration No.,Policy Expiry Date,Renewal Premium,Renewal Status\n"
    "IP0001,Demo Partner,RM0001,Demo Customer,9999999999,Car,Demo Insurer,POL123,MH15AB1234,20/08/2026,12500,Pending\n"
)

with app.test_client() as client:
    headers = {"Authorization": f"Bearer {token}"}

    policy = client.get("/api/p13/operational/import-policy", headers=headers)
    assert policy.status_code == 200, policy.get_data(as_text=True)
    body = policy.get_json()
    assert ".csv" in body["allowed_extensions"]

    response = client.post(
        "/api/p13/operational/import-file",
        headers=headers,
        data={
            "source_type": "renewal",
            "source_name": "Smoke Renewal Report",
            "dry_run": "true",
            "file": (io.BytesIO(csv_data.encode("utf-8")), "renewal_smoke.csv"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    preview = response.get_json()
    assert preview["new_rows"] == 1, preview
    assert preview["preview"][0]["partner_code"] == "IP0001"
    assert preview["preview"][0]["policy_number"] == "POL123"

    committed = client.post(
        "/api/p13/operational/import-file",
        headers=headers,
        data={
            "source_type": "renewal",
            "source_name": "Smoke Renewal Report",
            "dry_run": "false",
            "file": (io.BytesIO(csv_data.encode("utf-8")), "renewal_smoke.csv"),
        },
        content_type="multipart/form-data",
    )
    assert committed.status_code == 201, committed.get_data(as_text=True)
    result = committed.get_json()
    assert result["rows_imported"] == 1, result

    duplicate = client.post(
        "/api/p13/operational/import-file",
        headers=headers,
        data={
            "source_type": "renewal",
            "source_name": "Smoke Renewal Report",
            "dry_run": "false",
            "file": (io.BytesIO(csv_data.encode("utf-8")), "renewal_smoke.csv"),
        },
        content_type="multipart/form-data",
    )
    assert duplicate.status_code == 201, duplicate.get_data(as_text=True)
    duplicate_result = duplicate.get_json()
    assert duplicate_result["rows_imported"] == 0, duplicate_result

    stored = db.session.execute(db.select(OperationalDataRecord)).scalars().all()
    assert len(stored) == 1
    assert "IP Code" in stored[0].raw_payload

print("P13 operational file ingestion: PASS")
