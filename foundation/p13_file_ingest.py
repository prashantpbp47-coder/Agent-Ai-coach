"""Secure multipart CSV/XLSX ingestion for operational booking/renewal reports.

This layer preserves the existing P13 JSON importer and adds a file boundary for
real operational reports. Uploaded content is parsed in memory, normalized through
P13's existing row normalizer, deduplicated by row hash, and committed only after
validation. No uploaded files are persisted to disk or GitHub.
"""
from __future__ import annotations

import io
import os
from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models_p13 import OperationalDataRecord
from .p13_routes import _normalize_operational_row, audit, scope
from .security import require_role
from .models import new_id

bp = Blueprint("p13_file_ingest", __name__, url_prefix="/api/p13")

MAX_FILE_BYTES = int(os.getenv("P13_IMPORT_MAX_BYTES", str(10 * 1024 * 1024)))
MAX_ROWS = int(os.getenv("P13_IMPORT_MAX_ROWS", "10000"))
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


def _extension(filename: str) -> str:
    name = (filename or "").strip().lower()
    dot = name.rfind(".")
    return name[dot:] if dot >= 0 else ""


def _load_rows(file_storage, extension: str) -> list[dict]:
    import pandas as pd

    raw = file_storage.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("file_too_large")
    if not raw:
        raise ValueError("empty_file")

    if extension == ".csv":
        frame = pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False)
    else:
        # data_only=True prevents formulas from being interpreted as formulas;
        # this importer consumes stored cell values only.
        frame = pd.read_excel(io.BytesIO(raw), dtype=str, keep_default_na=False, engine="openpyxl")

    if frame.empty:
        raise ValueError("no_rows_found")
    if len(frame.index) > MAX_ROWS:
        raise ValueError("row_limit_exceeded")

    frame.columns = [str(c).strip() for c in frame.columns]
    if any(not c for c in frame.columns):
        raise ValueError("blank_header")
    if len(set(frame.columns)) != len(frame.columns):
        raise ValueError("duplicate_headers")

    rows = []
    for record in frame.to_dict(orient="records"):
        clean = {str(k).strip(): (None if v in ("", None) else str(v).strip()) for k, v in record.items()}
        if any(value not in (None, "") for value in clean.values()):
            rows.append(clean)
    return rows


@bp.post("/operational/import-file")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def import_operational_file():
    rm_id = scope()
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422

    uploaded = request.files.get("file")
    source_type = str(request.form.get("source_type") or "booking").strip().lower()
    source_name = str(request.form.get("source_name") or (uploaded.filename if uploaded else "operational_report")).strip()
    dry_run = str(request.form.get("dry_run") or "false").lower() in {"1", "true", "yes"}

    if not uploaded or not uploaded.filename:
        return jsonify({"error": "file_required"}), 400
    if source_type not in {"booking", "renewal", "partner_summary"}:
        return jsonify({"error": "unsupported_source_type"}), 400

    extension = _extension(uploaded.filename)
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "unsupported_file_type", "allowed": sorted(ALLOWED_EXTENSIONS)}), 415

    try:
        rows = _load_rows(uploaded, extension)
    except ValueError as exc:
        code = str(exc)
        status = 413 if code in {"file_too_large", "row_limit_exceeded"} else 400
        return jsonify({"error": code}), status
    except Exception as exc:
        return jsonify({"error": "file_parse_failed", "detail": str(exc)[:180]}), 400

    normalized_rows = []
    duplicate_in_file = 0
    seen = set()
    for raw in rows:
        normalized = _normalize_operational_row(raw, source_type, source_name)
        normalized["rm_id"] = rm_id
        if normalized["row_hash"] in seen:
            duplicate_in_file += 1
            continue
        seen.add(normalized["row_hash"])
        normalized_rows.append(normalized)

    existing_hashes = set()
    if normalized_rows:
        hashes = [r["row_hash"] for r in normalized_rows]
        for start in range(0, len(hashes), 500):
            chunk = hashes[start:start + 500]
            existing_hashes.update(
                x[0]
                for x in db.session.execute(
                    select(OperationalDataRecord.row_hash).where(OperationalDataRecord.row_hash.in_(chunk))
                ).all()
            )

    new_rows = [row for row in normalized_rows if row["row_hash"] not in existing_hashes]
    preview = []
    for row in new_rows[:10]:
        preview.append({
            "partner_code": row.get("partner_code"),
            "partner_name": row.get("partner_name"),
            "rm_code": row.get("rm_code"),
            "customer_name": row.get("customer_name"),
            "product": row.get("product"),
            "policy_number": row.get("policy_number"),
            "vehicle_number": row.get("vehicle_number"),
            "policy_expiry_date": row.get("policy_expiry_date").isoformat() if row.get("policy_expiry_date") else None,
            "premium": row.get("premium"),
            "status": row.get("status"),
        })

    if dry_run:
        return jsonify({
            "ok": True,
            "dry_run": True,
            "source_type": source_type,
            "source_name": source_name,
            "rows_received": len(rows),
            "rows_valid": len(normalized_rows),
            "duplicates_in_file": duplicate_in_file,
            "already_imported": len(normalized_rows) - len(new_rows),
            "new_rows": len(new_rows),
            "preview": preview,
        })

    user = getattr(request, "current_user", None)
    created = 0
    try:
        for row in new_rows:
            row["imported_by"] = user.id if user else None
            db.session.add(OperationalDataRecord(**row))
            created += 1
        audit("operational_data.file_import", "operational_data_record", None)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "ok": True,
        "dry_run": False,
        "source_type": source_type,
        "source_name": source_name,
        "rows_received": len(rows),
        "rows_imported": created,
        "duplicates_in_file": duplicate_in_file,
        "already_imported": len(normalized_rows) - len(new_rows),
        "new_rows": len(new_rows),
        "import_batch_id": new_id(),
    }), 201


@bp.get("/operational/import-policy")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def import_policy():
    return jsonify({
        "max_file_bytes": MAX_FILE_BYTES,
        "max_rows": MAX_ROWS,
        "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
        "supported_source_types": ["booking", "renewal", "partner_summary"],
        "storage": "normalized_fields_plus_raw_payload_in_database",
        "raw_files_persisted": False,
        "deduplication": "sha256(source_type|source_name|canonical_row)",
        "recommended_first_step": "dry_run=true",
    })
