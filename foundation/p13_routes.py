"""P13 business reconciliation, report APIs and operational data ingestion."""
from datetime import date, datetime, timezone
import hashlib
import json
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, AuditLog, RM
from .models_p4 import BusinessEvent, AgentContact, AgentDailyActivity, BusinessReconciliation
from .models_p13 import ExternalBusinessImport, OperationalDataRecord, BusinessReconciliationRun, BusinessReconciliationDetail, RMDailyReportSnapshot
from .security import current_user, require_role

bp = Blueprint("p13", __name__, url_prefix="/api/p13")

def today(): return date.today()
def now(): return datetime.now(timezone.utc)

def rm_for_user():
    u=current_user()
    if not u: return None
    return db.session.execute(select(RM).filter(func.lower(RM.email)==func.lower(u.email))).scalar_one_or_none()

def scope():
    req=request.args.get("rm_id") or (request.get_json(silent=True) or {}).get("rm_id")
    rm=rm_for_user(); admin=any(r.name=="ADMIN" for r in getattr(current_user(),"roles",[]))
    if req and rm and req != rm.id and not admin: return None
    return req or (rm.id if rm else None)

def audit(action, kind, rid=None):
    u=current_user(); db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid, user_id=u.id if u else None, request_id=str(uuid.uuid4()), ip_address=request.remote_addr))

def system_totals(rm_id, d):
    rows=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.business_date==d)).scalars().all()
    bycat={}; total=policies=0
    for row in rows:
        bycat.setdefault(row.category,{"premium":0,"policies":0})
        bycat[row.category]["premium"] += row.premium
        bycat[row.category]["policies"] += row.policies
        total += row.premium; policies += row.policies
    return total, policies, bycat

def _value(row, *names):
    lowered={str(k).strip().lower(): v for k,v in row.items()}
    for name in names:
        value=lowered.get(name.lower())
        if value not in (None, ""):
            return value
    return None

def _int_value(value):
    if value in (None, ""): return 0
    try:
        cleaned=str(value).replace(",", "").replace("₹", "").strip()
        return int(float(cleaned))
    except (TypeError, ValueError):
        return 0

def _date_value(value):
    if not value: return None
    text=str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y", "%d %b %Y"):
        try: return datetime.strptime(text[:10],fmt).date()
        except ValueError: pass
    return None

def _normalize_operational_row(row, source_type, source_name):
    payload=dict(row)
    source_reference=_value(payload,"lead id","leadid","lead_id","application no.","applicationno","applicationnumber","policy no.","policy_no","policy number","policy_number","booking id")
    partner_code=_value(payload,"ip code","partner code","partner_code","affiliatecode","affiliate code")
    partner_name=_value(payload,"partner name","partner_name","agentname","agent name")
    rm_code=_value(payload,"rm code","rm_code","parent code","parent_code")
    rm_name=_value(payload,"rm name","rm_name","parent name","parent_name")
    customer_name=_value(payload,"customer name","customer","insured name","insuredname","name")
    customer_mobile=_value(payload,"customer mobile no.","customer mobile","mobile no","mobile","mobileno","mobileno.","phone")
    product=_value(payload,"product","sub product")
    insurer=_value(payload,"insurer name","insurer","supplier name","suppliername")
    policy_number=_value(payload,"policy no.","policy no","policy number","policyno","previous policy number","previouspolicynumber")
    vehicle_number=_value(payload,"registration no.","registration number","registrationno","vehicle number","vehicle_number")
    policy_start=_date_value(_value(payload,"policy start date","policystartdate","policy start"))
    policy_expiry=_date_value(_value(payload,"policy expiry date","policyexpirydate","policy expiry","expiry date","policy expiry_date"))
    transaction_date=_date_value(_value(payload,"booking date","bookingdate","issuance date","issuance_date","transaction date","transaction_date","date"))
    premium=_int_value(_value(payload,"net premium","renewal premium","renewalpremium","premium","final amt","final amount","ape"))
    policies=_int_value(_value(payload,"nop","policies","policy count")) or 1
    status=_value(payload,"renewal status","status","renewed","disposition")
    canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    row_hash=hashlib.sha256((source_type+"|"+source_name+"|"+canonical).encode("utf-8")).hexdigest()
    return dict(source_type=source_type,source_name=source_name,source_reference=str(source_reference).strip() if source_reference not in (None,"") else None,row_hash=row_hash,partner_code=str(partner_code).strip() if partner_code not in (None,"") else None,partner_name=str(partner_name).strip() if partner_name not in (None,"") else None,rm_code=str(rm_code).strip() if rm_code not in (None,"") else None,rm_name=str(rm_name).strip() if rm_name not in (None,"") else None,customer_name=str(customer_name).strip() if customer_name not in (None,"") else None,customer_mobile=str(customer_mobile).strip() if customer_mobile not in (None,"") else None,product=str(product).strip() if product not in (None,"") else None,insurer=str(insurer).strip() if insurer not in (None,"") else None,policy_number=str(policy_number).strip() if policy_number not in (None,"") else None,vehicle_number=str(vehicle_number).strip() if vehicle_number not in (None,"") else None,policy_start_date=policy_start,policy_expiry_date=policy_expiry,transaction_date=transaction_date,premium=premium,policies=policies,status=str(status).strip() if status not in (None,"") else None,raw_payload=canonical)

@bp.post("/business/import")
@require_role("RM","MASTER_AGENT","ADMIN")
def import_business():
    data=request.get_json(silent=True) or {}; rm_id=scope()
    rows=data.get("rows")
    if not rm_id or not isinstance(rows,list): return jsonify({"error":"rm_mapping_and_rows_required"}),400
    created=0; skipped=0
    u=current_user()
    for row in rows:
        if not row.get("source_name") or not row.get("category"): continue
        ref=str(row.get("source_reference") or "").strip() or None
        policy=str(row.get("policy_reference") or "").strip() or None
        stmt=select(ExternalBusinessImport).where(ExternalBusinessImport.rm_id==rm_id,ExternalBusinessImport.source_name==row["source_name"],ExternalBusinessImport.source_reference==ref,ExternalBusinessImport.policy_reference==policy)
        existing=db.session.execute(stmt).scalar_one_or_none()
        if existing: skipped+=1; continue
        db.session.add(ExternalBusinessImport(rm_id=rm_id,import_date=date.fromisoformat(row.get("import_date")) if row.get("import_date") else today(),source_name=row["source_name"],source_reference=ref,category=row["category"],agent_code=row.get("agent_code"),policy_reference=policy,premium=int(row.get("premium",0)),policies=int(row.get("policies",0)),imported_by=u.id if u else None,raw_row_json=json.dumps(row,ensure_ascii=False)))
        created+=1
    audit("business.external_import","external_business_import",None); db.session.commit()
    return jsonify({"created":created,"skipped":skipped})

@bp.post("/operational/import")
@require_role("RM","MASTER_AGENT","ADMIN")
def import_operational_rows():
    """Import complete booking/renewal rows without losing source columns."""
    data=request.get_json(silent=True) or {}
    rows=data.get("rows")
    source_type=str(data.get("source_type") or "booking").strip().lower()
    source_name=str(data.get("source_name") or "operational_report").strip()
    rm_id=scope()
    if not rm_id or not isinstance(rows,list): return jsonify({"error":"rm_mapping_and_rows_required"}),400
    if source_type not in {"booking","renewal","partner_summary"}: return jsonify({"error":"unsupported_source_type"}),400
    user=current_user(); created=skipped=0
    try:
        for raw in rows:
            if not isinstance(raw,dict): continue
            normalized=_normalize_operational_row(raw,source_type,source_name)
            normalized["rm_id"]=rm_id; normalized["imported_by"]=user.id if user else None
            existing=db.session.execute(select(OperationalDataRecord).filter_by(row_hash=normalized["row_hash"])).scalar_one_or_none()
            if existing: skipped+=1; continue
            db.session.add(OperationalDataRecord(**normalized)); created+=1
        audit("operational_data.import", "operational_data_record", None); db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({"source_type":source_type,"source_name":source_name,"created":created,"skipped":skipped,"total_received":len(rows)})

@bp.get("/operational/partner-summary")
@require_role("RM","MASTER_AGENT","ADMIN")
def operational_partner_summary():
    """Partner-wise business and renewal intelligence from imported source rows."""
    rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    source_type=request.args.get("source_type")
    q=select(OperationalDataRecord).where(OperationalDataRecord.rm_id==rm_id)
    if source_type: q=q.where(OperationalDataRecord.source_type==source_type)
    rows=db.session.execute(q).scalars().all()
    grouped={}
    for row in rows:
        key=row.partner_code or row.partner_name or "UNMAPPED"
        item=grouped.setdefault(key,{"partner_code":row.partner_code,"partner_name":row.partner_name or "Unmapped","rm_code":row.rm_code,"rm_name":row.rm_name,"booking_nop":0,"booking_premium":0,"renewal_opportunities":0,"renewal_premium":0,"renewed":0,"pending_followups":0,"customers":set(),"last_transaction":None})
        if row.source_type=="booking": item["booking_nop"]+=row.policies; item["booking_premium"]+=row.premium
        if row.source_type=="renewal":
            item["renewal_opportunities"]+=1; item["renewal_premium"]+=row.premium
            if str(row.status or "").lower() in {"renewed","yes","success"}: item["renewed"]+=1
        if row.customer_name: item["customers"].add(row.customer_name)
        if row.transaction_date and (not item["last_transaction"] or row.transaction_date>item["last_transaction"]): item["last_transaction"]=row.transaction_date
    items=[]
    for item in grouped.values():
        item["customer_count"]=len(item.pop("customers")); item["last_transaction"]=item["last_transaction"].isoformat() if item["last_transaction"] else None
        items.append(item)
    items.sort(key=lambda x:(x["booking_premium"],x["renewal_premium"]),reverse=True)
    return jsonify({"count":len(items),"items":items})

@bp.get("/operational/renewals")
@require_role("RM","MASTER_AGENT","ADMIN")
def operational_renewals():
    rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    days=int(request.args.get("days",30))
    cutoff=today().fromordinal(today().toordinal()+days)
    rows=db.session.execute(select(OperationalDataRecord).where(OperationalDataRecord.rm_id==rm_id,OperationalDataRecord.source_type=="renewal",OperationalDataRecord.policy_expiry_date.is_not(None),OperationalDataRecord.policy_expiry_date<=cutoff).order_by(OperationalDataRecord.policy_expiry_date.asc())).scalars().all()
    return jsonify({"count":len(rows),"items":[{"id":r.id,"partner_code":r.partner_code,"partner_name":r.partner_name,"customer_name":r.customer_name,"mobile":r.customer_mobile,"vehicle_number":r.vehicle_number,"product":r.product,"insurer":r.insurer,"policy_number":r.policy_number,"expiry_date":r.policy_expiry_date.isoformat() if r.policy_expiry_date else None,"premium":r.premium,"status":r.status,"source_name":r.source_name} for r in rows]})

@bp.post("/reconcile")
@require_role("RM","MASTER_AGENT","ADMIN")
def reconcile():
    data=request.get_json(silent=True) or {}; rm_id=scope()
    d=date.fromisoformat(data.get("date")) if data.get("date") else today(); source=data.get("source_name","external_import")
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    ext_rows=db.session.execute(select(ExternalBusinessImport).where(ExternalBusinessImport.rm_id==rm_id,ExternalBusinessImport.import_date==d,ExternalBusinessImport.source_name==source)).scalars().all()
    source_bycat={}; sp=0; sc=0
    for row in ext_rows:
        source_bycat.setdefault(row.category,{"premium":0,"policies":0}); source_bycat[row.category]["premium"]+=row.premium; source_bycat[row.category]["policies"]+=row.policies; sp+=row.premium; sc+=row.policies
    sys_total, sys_policies, system_bycat=system_totals(rm_id,d)
    cats=sorted(set(source_bycat)|set(system_bycat)); tolerance=int(data.get("tolerance_premium",0)); policy_tol=int(data.get("tolerance_policies",0))
    run=BusinessReconciliationRun(rm_id=rm_id,reconciliation_date=d,source_name=source,tolerance_premium=tolerance,tolerance_policies=policy_tol,source_total=sp,source_policies=sc,system_total=sys_total,system_policies=sys_policies,premium_difference=sys_total-sp,policy_difference=sys_policies-sc,status="matched" if abs(sys_total-sp)<=tolerance and abs(sys_policies-sc)<=policy_tol else "mismatch")
    db.session.add(run); db.session.flush()
    mismatches=0
    for cat in cats:
        s=source_bycat.get(cat,{"premium":0,"policies":0}); x=system_bycat.get(cat,{"premium":0,"policies":0}); sd=s["premium"]-x["premium"]; scd=s["policies"]-x["policies"]; status="matched" if abs(sd)<=tolerance and abs(scd)<=policy_tol else "mismatch"
        if status!="matched": mismatches+=1
        db.session.add(BusinessReconciliationDetail(run_id=run.id,category=cat,source_premium=s["premium"],system_premium=x["premium"],source_policies=s["policies"],system_policies=x["policies"],premium_difference=sd,policy_difference=scd,status=status))
    audit("business.reconciliation","business_reconciliation_run",run.id); db.session.commit()
    return jsonify({"run_id":run.id,"status":run.status,"source_total":sp,"system_total":sys_total,"premium_difference":run.premium_difference,"source_policies":sc,"system_policies":sys_policies,"policy_difference":run.policy_difference,"category_mismatches":mismatches})

@bp.get("/reconciliation")
@require_role("RM","MASTER_AGENT","ADMIN")
def reconciliation_list():
    rm_id=scope(); d=date.fromisoformat(request.args.get("date")) if request.args.get("date") else today()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    runs=db.session.execute(select(BusinessReconciliationRun).where(BusinessReconciliationRun.rm_id==rm_id,BusinessReconciliationRun.reconciliation_date==d).order_by(BusinessReconciliationRun.created_at.desc())).scalars().all()
    return jsonify({"items":[{"id":r.id,"source":r.source_name,"status":r.status,"source_total":r.source_total,"system_total":r.system_total,"premium_difference":r.premium_difference,"policy_difference":r.policy_difference,"created_at":r.created_at.isoformat()} for r in runs]})

@bp.post("/daily-report")
@require_role("RM","MASTER_AGENT","ADMIN")
def daily_report():
    rm_id=scope(); payload=request.get_json(silent=True) or {}; d=date.fromisoformat(payload.get("date")) if payload.get("date") else today()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    sys_total,_,_=system_totals(rm_id,d)
    active=db.session.scalar(select(func.count()).select_from(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d,AgentDailyActivity.active_today.is_(True))) or 0
    calls=db.session.scalar(select(func.count()).select_from(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.contact_date==d)) or 0
    meetings=db.session.execute(select(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d)).scalars().all(); projected=sum(x.projected_premium for x in meetings); high_value=sum(1 for x in meetings if x.actual_premium>=10000 or x.projected_premium>=10000)
    mismatches=db.session.scalar(select(func.count()).select_from(BusinessReconciliationRun).where(BusinessReconciliationRun.rm_id==rm_id,BusinessReconciliationRun.reconciliation_date==d,BusinessReconciliationRun.status=="mismatch")) or 0
    row=db.session.execute(select(RMDailyReportSnapshot).where(RMDailyReportSnapshot.rm_id==rm_id,RMDailyReportSnapshot.report_date==d)).scalar_one_or_none()
    if not row: row=RMDailyReportSnapshot(rm_id=rm_id,report_date=d); db.session.add(row)
    row.actual_premium=sys_total; row.projected_premium=projected; row.target_premium=500000; row.active_agents=active; row.calls_completed=calls; row.meetings_completed=len(meetings); row.new_agent_meetings=0; row.high_value_agents=high_value; row.mismatch_count=mismatches
    db.session.commit()
    return jsonify({"date":str(d),"actual_premium":sys_total,"projected_premium":projected,"target_premium":row.target_premium,"gap_to_target":max(row.target_premium-sys_total,0),"active_agents":active,"calls_completed":calls,"meetings_completed":len(meetings),"high_value_agents":high_value,"reconciliation_mismatches":mismatches})

@bp.get("/agent-performance")
@require_role("RM","MASTER_AGENT","ADMIN")
def agent_performance():
    rm_id=scope(); d=date.fromisoformat(request.args.get("date")) if request.args.get("date") else today()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id)).scalars().all(); out=[]
    for a in agents:
        events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.agent_id==a.id,BusinessEvent.business_date==d)).scalars().all()
        out.append({"agent_id":a.id,"partner_code":a.partner_code,"name":a.name,"premium":sum(e.premium for e in events),"policies":sum(e.policies for e in events),"categories":{c:sum(e.premium for e in events if e.category==c) for c in sorted({e.category for e in events})}})
    return jsonify({"date":str(d),"items":out})

@bp.get("/command-center")
@require_role("RM","MASTER_AGENT","ADMIN")
def command_center():
    """Management dashboard payload using existing P4/P13 operational data.

    RM scope is enforced; the internal RM target is never returned to agent roles.
    """
    rm_id=scope(); d=date.fromisoformat(request.args.get("date")) if request.args.get("date") else today()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    total, policies, bycat=system_totals(rm_id,d); active=db.session.scalar(select(func.count()).select_from(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d,AgentDailyActivity.active_today.is_(True))) or 0
    calls=db.session.scalar(select(func.count()).select_from(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.contact_date==d)) or 0
    activities=db.session.execute(select(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d)).scalars().all(); projected=sum(x.projected_premium for x in activities)
    agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id)).scalars().all(); partner_rows=[]
    for a in agents:
        events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.agent_id==a.id,BusinessEvent.business_date==d)).scalars().all(); premium=sum(e.premium for e in events); nops=sum(e.policies for e in events); partner_rows.append({"partner_code":a.partner_code,"partner_name":a.name,"nop":nops,"net_premium":premium})
    partner_rows.sort(key=lambda x:x["net_premium"], reverse=True)
    return jsonify({"date":str(d),"kpis":{"actual_premium":total,"policies":policies,"active_partners":active,"calls":calls,"projected_premium":projected},"internal_rm_target":500000,"target_gap":max(500000-total,0),"category_breakdown":bycat,"partner_performance":partner_rows,"next_best_actions":[{"priority":"high","action":"Contact highest-value active partners first","count":sum(1 for x in partner_rows if x["net_premium"]>=10000)},{"priority":"medium","action":"Complete daily partner calls","gap":max(20-calls,0)},{"priority":"medium","action":"Review projected business before end of day","projected_premium":projected}]})
