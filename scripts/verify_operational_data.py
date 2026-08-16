#!/usr/bin/env python3
"""Deterministic operational-data contract test.

Uses representative booking, partner-summary and renewal rows only. No
production/customer file is embedded here. The test verifies that the
normalizer preserves the complete source payload while mapping the common
business fields required by Partner-wise and Renewal reporting.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from foundation.p13_routes import _normalize_operational_row


REQUIRED_KEYS = {
    "source_type",
    "source_name",
    "row_hash",
    "partner_code",
    "partner_name",
    "rm_code",
    "rm_name",
    "customer_name",
    "customer_mobile",
    "product",
    "insurer",
    "policy_number",
    "vehicle_number",
    "policy_start_date",
    "policy_expiry_date",
    "transaction_date",
    "premium",
    "policies",
    "status",
    "raw_payload",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    booking = {
        "Lead ID": "BK-1001",
        "IP Code": "IP250227",
        "Partner Name": "Test Partner",
        "RM Code": "RM001",
        "RM Name": "Test RM",
        "Customer Name": "Test Customer",
        "Customer Mobile No.": "9999999999",
        "Product": "Car",
        "Insurer Name": "Test Insurer",
        "Policy No.": "POL-1001",
        "Registration No.": "MH15AB1234",
        "Booking Date": "2026-08-16",
        "Premium": "12,500",
        "NOP": "1",
        "Status": "Booked",
    }

    renewal = {
        "leadId": "RN-2001",
        "affiliateCode": "IP250227",
        "agentName": "Test Partner",
        "customer": "Renewal Customer",
        "mobileNo": "8888888888",
        "product": "Car",
        "supplierName": "Test Insurer",
        "policyNo": "POL-2001",
        "registrationNo": "MH15CD5678",
        "policyExpiryDate": "2026-08-30",
        "renewalPremium": "18,750",
        "renewalStatus": "Pending",
    }

    for source_type, source_name, row in (
        ("booking", "Booking Report", booking),
        ("renewal", "Renewal Report", renewal),
    ):
        normalized = _normalize_operational_row(row, source_type, source_name)
        check(REQUIRED_KEYS <= normalized.keys(), f"missing keys for {source_type}")
        check(normalized["source_type"] == source_type, f"wrong source type: {source_type}")
        check(bool(normalized["row_hash"]) and len(normalized["row_hash"]) == 64, f"invalid hash: {source_type}")
        original = json.loads(normalized["raw_payload"])
        check(original == row, f"raw payload was not lossless for {source_type}")
        check(normalized["partner_code"] == "IP250227", f"partner code mapping failed: {source_type}")
        check(normalized["partner_name"] == "Test Partner", f"partner name mapping failed: {source_type}")
        check(normalized["premium"] > 0, f"premium mapping failed: {source_type}")

    print("OPERATIONAL DATA CONTRACT: PASS")
    print("Booking mapping: PASS")
    print("Renewal mapping: PASS")
    print("Lossless raw payload: PASS")
    print("Partner-code mapping: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"OPERATIONAL DATA CONTRACT: FAIL — {exc}", file=sys.stderr)
        raise
