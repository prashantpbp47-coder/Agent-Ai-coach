"""P12 Clay-compatible prospect research ingestion and scoring APIs."""
import json
import uuid
from datetime import date
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import AuditLog, RM
from .models_p5 import AgentProspect
from .models_p12 import ClayResearchRun, ProspectIntelligence, ProspectSourceRecord
from .security import current_user, require_role

bp = Blueprint("p12", __name__, url_prefix="/api/p12")


def audit(action, kind, rid=None):
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid, user_id=u.id if u else None,
                            request_id=str(uuid.uuid4()), ip_address=request.remote_addr))


def rm_for_user():
    u = current_user()
    if not u:
        return None
    return db.session.execute(select(RM).filter(func.lower(RM.email) == func.lower(u.email))).scalar_one_or_none()


def scope_rm():
    data = request.get_json(silent=True) or {}
    requested = request.args.get("rm_id") or data.get("rm_id")
    rm = rm_for_user()
    is_admin = any(r.name == "ADMIN" for r in getattr(current_user(), "roles", []))
    if requested and rm and requested != rm.id and not is_admin:
        return None
    return requested or (rm.id if rm else None)


def score_row(row, area=None):
    fit = 0
    profession = str(row.get("profession") or "").lower()
    if any(term in profession for term in ("insurance", "finance", "bank", "loan", "automobile", "car", "bike", "dealer", "real estate")):
        fit = 30
    elif profession:
        fit = 15
    area_score = 25 if area and str(row.get("area") or "").strip().lower() == str(area).strip().lower() else (15 if row.get("area") else 0)
    evidence = 20 if row.get("source_url") or row.get("evidence") else 5
    potential = 15 if row.get("business_potential") else 5
    relationship = 10 if row.get("relationship_context") else 0
    total = min(fit + area_score + evidence + potential + relationship, 100)
    return total, fit, area_score, evidence, potential, relationship


@bp.post("/clay/import")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def clay_import():
    data = request.get_json(silent=True) or {}
    rm_id = scope_rm()
    rows = data.get("rows")
    area = str(data.get("area") or "").strip() or None
    pincode = str(data.get("pincode") or "").strip() or None
    if not rm_id or not isinstance(rows, list):
        return jsonify({"error": "rm_mapping_and_rows_required"}), 400
    run = ClayResearchRun(rm_id=rm_id, area=area, pincode=pincode, source="clay", status="received", row_count=len(rows))
    db.session.add(run); db.session.flush()
    created = updated = 0
    for row in rows[:200]:
        if not isinstance(row, dict) or not str(row.get("name") or "").strip():
            continue
        phone = row.get("phone")
        existing = None
        if phone:
            existing = db.session.execute(select(AgentProspect).where(AgentProspect.rm_id == rm_id, AgentProspect.phone == str(phone))).scalar_one_or_none()
        if not existing:
            existing = AgentProspect(rm_id=rm_id, name=str(row["name"]).strip(), phone=str(phone) if phone else None,
                                     area=row.get("area") or area, pincode=row.get("pincode") or pincode,
                                     profession=row.get("profession"), source="clay", source_url=row.get("source_url"),
                                     evidence=row.get("evidence"), consent_status=row.get("consent_status", "unknown"), status="candidate")
            db.session.add(existing); db.session.flush(); created += 1
        else:
            existing.name = str(row["name"]).strip()
            if row.get("area"): existing.area = row["area"]
            if row.get("pincode"): existing.pincode = row["pincode"]
            if row.get("profession"): existing.profession = row["profession"]
            if row.get("source_url"): existing.source_url = row["source_url"]
            if row.get("evidence"): existing.evidence = row["evidence"]
            updated += 1
        total, fit, area_score, evidence, potential, relationship = score_row(row, area)
        intel = db.session.execute(select(ProspectIntelligence).filter_by(prospect_id=existing.id)).scalar_one_or_none()
        if not intel:
            intel = ProspectIntelligence(prospect_id=existing.id)
            db.session.add(intel)
        intel.score = total; intel.fit_score = fit; intel.area_score = area_score; intel.evidence_score = evidence
        intel.business_potential_score = potential; intel.relationship_score = relationship
        intel.recommendation = "Prioritize for RM new-agent meeting" if total >= 70 else ("Review for RM outreach" if total >= 50 else "Keep in prospect pool")
        intel.research_json = json.dumps(row, ensure_ascii=False)
        if row.get("source_url") or row.get("external_id"):
            src = db.session.execute(select(ProspectSourceRecord).where(ProspectSourceRecord.provider == "clay", ProspectSourceRecord.external_id == row.get("external_id"))).scalar_one_or_none() if row.get("external_id") else None
            if not src and row.get("external_id"):
                src = ProspectSourceRecord(prospect_id=existing.id, provider="clay", external_id=str(row["external_id"]), source_url=row.get("source_url"), raw_json=json.dumps(row, ensure_ascii=False))
                db.session.add(src)
        audit("clay.prospect.import", "agent_prospect", existing.id)
    run.status = "processed"; db.session.commit()
    return jsonify({"run_id": run.id, "created": created, "updated": updated, "rows_received": len(rows)})


@bp.get("/prospects/recommended")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def recommended():
    rm_id = scope_rm()
    area = request.args.get("area")
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422
    q = select(AgentProspect, ProspectIntelligence).join(ProspectIntelligence, ProspectIntelligence.prospect_id == AgentProspect.id).where(AgentProspect.rm_id == rm_id, AgentProspect.status == "candidate")
    if area:
        q = q.where(func.lower(AgentProspect.area) == area.lower())
    rows = db.session.execute(q.order_by(ProspectIntelligence.score.desc()).limit(10)).all()
    return jsonify({"area": area, "recommendations": [
        {"prospect_id": p.id, "name": p.name, "phone": p.phone, "area": p.area, "pincode": p.pincode, "profession": p.profession,
         "source": p.source, "source_url": p.source_url, "consent_status": p.consent_status, "score": i.score,
         "recommendation": i.recommendation} for p, i in rows
    ]})


@bp.get("/health")
def health():
    return jsonify({"provider": "clay", "mode": "ingestion_boundary", "status": "ready"})
