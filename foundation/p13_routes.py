"""P13 business reconciliation and report APIs."""
from datetime import date, datetime, timezone
import json
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, BusinessEvent, AuditLog, RM
from .models_p4 import AgentContact, AgentDailyActivity, BusinessReconciliation
from .models_p13 import ExternalBusinessImport, BusinessReconciliationRun, BusinessReconciliationDetail, RMDailyReportSnapshot
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

@bp.post("/business/import")
@require_role("RM","MASTER_AGENT","ADMIN")
def import_business():
    data=request.get_json(silent=True) or {}; rm_id=scope()
    rows=data.get("rows")
    if not rm_id or not isinstance(rows,list): return jsonify({"error":"rm_mapping_and_rows_required"}),400
    created=0; skipped=0
    u=current_user()
    for row in rows:
        if not row.get("source_name") or not row.get("category"):
            continue
        ref=str(row.get("source_reference") or "").strip() or None
        policy=str(row.get("policy_reference") or "").strip() or None
        stmt=select(ExternalBusinessImport).where(ExternalBusinessImport.rm_id==rm_id,ExternalBusinessImport.source_name==row["source_name"],ExternalBusinessImport.source_reference==ref,ExternalBusinessImport.policy_reference==policy)
        existing=db.session.execute(stmt).scalar_one_or_none()
        if existing:
            skipped+=1; continue
        db.session.add(ExternalBusinessImport(rm_id=rm_id,import_date=date.fromisoformat(row.get("import_date")) if row.get("import_date") else today(),source_name=row["source_name"],source_reference=ref,category=row["category"],agent_code=row.get("agent_code"),policy_reference=policy,premium=int(row.get("premium",0)),policies=int(row.get("policies",0)),imported_by=u.id if u else None,raw_row_json=json.dumps(row,ensure_ascii=False)))
        created+=1
    audit("business.external_import","external_business_import",None); db.session.commit()
    return jsonify({"created":created,"skipped":skipped})

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
        s=source_bycat.get(cat,{"premium":0,"policies":0}); x=system_bycat.get(cat,{"premium":0,"policies":0})
        sd=s["premium"]-x["premium"]; scd=s["policies"]-x["policies"]; status="matched" if abs(sd)<=tolerance and abs(scd)<=policy_tol else "mismatch"
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
    rm_id=scope(); d=date.fromisoformat((request.get_json(silent=True) or {}).get("date")) if (request.get_json(silent=True) or {}).get("date") else today()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    sys_total,_,_=system_totals(rm_id,d)
    active=db.session.scalar(select(func.count()).select_from(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d,AgentDailyActivity.active_today.is_(True))) or 0
    calls=db.session.scalar(select(func.count()).select_from(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.contact_date==d)) or 0
    meetings=db.session.execute(select(AgentDailyActivity).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==d)).scalars().all()
    projected=sum(x.projected_premium for x in meetings)
    high_value=sum(1 for x in meetings if x.actual_premium>=10000 or x.projected_premium>=10000)
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
    agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id)).scalars().all()
    out=[]
    for a in agents:
        events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.agent_id==a.id,BusinessEvent.business_date==d)).scalars().all()
        out.append({"agent_id":a.id,"partner_code":a.partner_code,"name":a.name,"premium":sum(e.premium for e in events),"policies":sum(e.policies for e in events),"categories":{c:sum(e.premium for e in events if e.category==c) for c in sorted({e.category for e in events})}})
    return jsonify({"date":str(d),"items":out})
