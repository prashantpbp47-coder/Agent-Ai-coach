"""P9 provider-neutral document/OCR intake and verification APIs."""
import json
import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import select
from .db import db
from .models import AuditLog, CustomerDocument, Customer, Lead
from .models_p9 import DocumentExtraction, DocumentVerification, VehicleIntelligence
from .security import current_user, require_permission

bp = Blueprint("p9", __name__, url_prefix="/api/p9")


def now(): return datetime.now(timezone.utc)

def audit(action, kind, rid=None):
    u=current_user(); db.session.add(AuditLog(action=action,resource_type=kind,resource_id=rid,user_id=u.id if u else None,request_id=str(uuid.uuid4()),ip_address=request.remote_addr))

@bp.post("/documents")
@require_permission("customers:write")
def create_document():
    d=request.get_json(silent=True) or {}
    if not d.get("customer_id") or not d.get("document_type"):
        return jsonify({"error":"customer_id_and_document_type_required"}),400
    if not db.session.get(Customer,d["customer_id"]): return jsonify({"error":"customer_not_found"}),404
    row=CustomerDocument(customer_id=d["customer_id"],lead_id=d.get("lead_id"),document_type=d["document_type"],storage_url=d.get("storage_url"),ocr_status="pending",verified=False)
    db.session.add(row); db.session.flush(); audit("document.intake","customer_document",row.id); db.session.commit()
    return jsonify({"document_id":row.id,"ocr_status":row.ocr_status,"verified":row.verified}),201

@bp.get("/documents/<document_id>")
@require_permission("customers:read")
def document(document_id):
    row=db.session.get(CustomerDocument,document_id)
    if not row: return jsonify({"error":"document_not_found"}),404
    extraction=db.session.execute(select(DocumentExtraction).where(DocumentExtraction.document_id==row.id).order_by(DocumentExtraction.created_at.desc()).limit(1)).scalar_one_or_none()
    vehicle=db.session.execute(select(VehicleIntelligence).filter_by(document_id=row.id)).scalar_one_or_none()
    return jsonify({"document_id":row.id,"customer_id":row.customer_id,"lead_id":row.lead_id,"document_type":row.document_type,"ocr_status":row.ocr_status,"verified":row.verified,"extraction":({"id":extraction.id,"status":extraction.status,"provider":extraction.provider,"fields":json.loads(extraction.fields_json or "{}"),"confidence":json.loads(extraction.confidence_json or "{}"),"error":extraction.error_message} if extraction else None),"vehicle":({"registration_number":vehicle.registration_number,"owner_name":vehicle.owner_name,"make":vehicle.make,"model":vehicle.model,"variant":vehicle.variant,"registration_date":vehicle.registration_date,"fuel_type":vehicle.fuel_type,"policy_expiry":vehicle.policy_expiry,"verified":vehicle.verified} if vehicle else None)})

@bp.post("/documents/<document_id>/extractions")
@require_permission("customers:write")
def extraction(document_id):
    row=db.session.get(CustomerDocument,document_id)
    if not row: return jsonify({"error":"document_not_found"}),404
    d=request.get_json(silent=True) or {}
    fields=d.get("fields") or {}
    ex=DocumentExtraction(document_id=row.id,provider=d.get("provider"),document_type=row.document_type,status=d.get("status","completed"),raw_text=d.get("raw_text"),fields_json=json.dumps(fields,default=str),confidence_json=json.dumps(d.get("confidence") or {},default=str),error_message=d.get("error"),completed_at=now() if d.get("status","completed") in {"completed","failed"} else None)
    db.session.add(ex)
    row.ocr_status=ex.status
    if row.document_type in {"rc","registration_certificate"}:
        vi=db.session.execute(select(VehicleIntelligence).filter_by(document_id=row.id)).scalar_one_or_none()
        if not vi: vi=VehicleIntelligence(document_id=row.id); db.session.add(vi)
        vi.registration_number=fields.get("registration_number") or fields.get("vehicle_number")
        vi.owner_name=fields.get("owner_name"); vi.make=fields.get("make"); vi.model=fields.get("model"); vi.variant=fields.get("variant"); vi.registration_date=fields.get("registration_date"); vi.fuel_type=fields.get("fuel_type"); vi.chassis_last4=fields.get("chassis_last4"); vi.engine_last4=fields.get("engine_last4"); vi.policy_expiry=fields.get("policy_expiry"); vi.confidence=str((d.get("confidence") or {}).get("registration_number", "")) or None
    audit("document.extraction","document_extraction",ex.id); db.session.commit()
    return jsonify({"extraction_id":ex.id,"document_id":row.id,"ocr_status":row.ocr_status,"verification_required":not row.verified}),201

@bp.post("/documents/<document_id>/verify")
@require_permission("customers:write")
def verify(document_id):
    row=db.session.get(CustomerDocument,document_id)
    if not row: return jsonify({"error":"document_not_found"}),404
    d=request.get_json(silent=True) or {}
    verified=bool(d.get("verified",False)); u=current_user()
    v=DocumentVerification(document_id=row.id,verified=verified,verified_by=u.id if u else None,verified_at=now(),corrections_json=json.dumps(d.get("corrections") or {},default=str))
    db.session.add(v); row.verified=verified
    vehicle=db.session.execute(select(VehicleIntelligence).filter_by(document_id=row.id)).scalar_one_or_none()
    if vehicle: vehicle.verified=verified
    audit("document.verify","customer_document",row.id); db.session.commit()
    return jsonify({"document_id":row.id,"verified":verified,"verified_by":u.id if u else None})

@bp.post("/documents/<document_id>/quote-ready")
@require_permission("quotes:write")
def quote_ready(document_id):
    row=db.session.get(CustomerDocument,document_id)
    if not row: return jsonify({"error":"document_not_found"}),404
    if not row.verified: return jsonify({"error":"document_verification_required"}),409
    vehicle=db.session.execute(select(VehicleIntelligence).filter_by(document_id=row.id)).scalar_one_or_none()
    if not vehicle or not vehicle.registration_number: return jsonify({"error":"vehicle_data_missing"}),422
    return jsonify({"quote_ready":True,"registration_number":vehicle.registration_number,"make":vehicle.make,"model":vehicle.model,"policy_expiry":vehicle.policy_expiry,"approved_provider_required":True})
