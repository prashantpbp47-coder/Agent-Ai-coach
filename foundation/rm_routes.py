"""RM daily command-center APIs for PartnersHub AI."""
import csv, io, uuid
from datetime import date, datetime, timedelta, timezone
from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, AuditLog, RM
from .models_p4 import AgentContact, AgentDailyActivity, AgentHierarchy, BusinessEvent, BusinessReconciliation, RMDailyTarget
from .security import current_user, require_permission, require_role
bp = Blueprint("rm_command_center", __name__, url_prefix="/api/rm")

def now_utc(): return datetime.now(timezone.utc)
def today(): return date.today()
def roles(): return {r.name for r in getattr(current_user(), "roles", [])}
def admin(): return "ADMIN" in roles()
def rm_for_user():
    u=current_user(); return db.session.execute(select(RM).filter(func.lower(RM.email)==func.lower(u.email))).scalar_one_or_none() if u else None
def rm_scope():
    data=request.get_json(silent=True) or {}; explicit=request.args.get("rm_id") or data.get("rm_id"); rm=rm_for_user()
    if explicit and rm and explicit!=rm.id and not admin(): return None
    return explicit or (rm.id if rm else None)
def audit(action, resource_type, resource_id=None):
    u=current_user(); db.session.add(AuditLog(action=action,resource_type=resource_type,resource_id=resource_id,user_id=u.id if u else None,request_id=str(uuid.uuid4()),ip_address=request.remote_addr))
def dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00")) if v else None

def target_for(rm_id):
    row=db.session.execute(select(RMDailyTarget).filter_by(rm_id=rm_id,target_date=today())).scalar_one_or_none()
    if not row:
        row=RMDailyTarget(rm_id=rm_id,target_date=today(),call_target=20,active_agent_target=5,high_value_agent_target=3,high_value_threshold=10000); db.session.add(row); db.session.flush()
    return row

@bp.get("/daily-plan")
@require_role("RM","MASTER_AGENT","ADMIN")
def daily_plan():
    rm_id=rm_scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    t=target_for(rm_id); excluded=select(AgentContact.agent_id).where(AgentContact.rm_id==rm_id,AgentContact.contact_date==today(),AgentContact.follow_up_required.is_(False))
    agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id,Agent.status=="active",Agent.id.not_in(excluded))).scalars().all(); rows=[]; cutoff=now_utc()-timedelta(days=7)
    for a in agents:
        last=db.session.execute(select(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.agent_id==a.id).order_by(AgentContact.created_at.desc()).limit(1)).scalar_one_or_none(); act=db.session.execute(select(AgentDailyActivity).filter_by(agent_id=a.id,activity_date=today())).scalar_one_or_none(); score=500 if not last else 0; reason="never_contacted" if not last else "pending_contact"
        if last and last.follow_up_required and (not last.follow_up_due_at or last.follow_up_due_at<=now_utc()): score+=1000; reason="follow_up_due"
        elif last and last.created_at<cutoff: score+=250; reason="stale_contact"
        if act and not act.active_today: score+=125; reason="activation_gap"
        rows.append({"agent_id":a.id,"partner_code":a.partner_code,"name":a.name,"phone":a.phone,"priority_score":score,"reason":reason,"last_contact_at":last.created_at.isoformat() if last else None,"follow_up_due_at":last.follow_up_due_at.isoformat() if last and last.follow_up_due_at else None,"active_today":bool(act.active_today) if act else False,"projected_premium":act.projected_premium if act else 0})
    rows.sort(key=lambda r:(-r["priority_score"],r["name"]))
    return jsonify({"date":str(today()),"rm_id":rm_id,"targets":{"calls":t.call_target,"active_agents":t.active_agent_target,"high_value_agents":t.high_value_agent_target,"high_value_threshold":t.high_value_threshold},"queue_count":min(len(rows),t.call_target),"queue":rows[:t.call_target]})

@bp.post("/contact")
@require_permission("agents:write")
def contact():
    data=request.get_json(silent=True) or {}; rm_id=rm_scope(); aid=data.get("agent_id")
    if not rm_id or not aid: return jsonify({"error":"rm_id_and_agent_id_required"}),400
    a=db.session.get(Agent,aid)
    if not a or a.rm_id!=rm_id: return jsonify({"error":"agent_not_in_rm_scope"}),404
    existing=db.session.execute(select(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.agent_id==aid,AgentContact.contact_date==today(),AgentContact.follow_up_required.is_(False))).first()
    if existing: return jsonify({"error":"already_contacted_today","agent_id":aid,"message":"Agent is excluded from today's call queue unless follow-up is required."}),409
    c=AgentContact(rm_id=rm_id,agent_id=aid,contact_date=today(),channel=data.get("channel","call"),outcome=data.get("outcome","contacted"),remarks=data.get("remarks"),follow_up_required=bool(data.get("follow_up_required",False)),follow_up_due_at=dt(data.get("follow_up_due_at")),call_reference=data.get("call_reference")); db.session.add(c)
    act=db.session.execute(select(AgentDailyActivity).filter_by(agent_id=aid,activity_date=today())).scalar_one_or_none()
    if not act: act=AgentDailyActivity(agent_id=aid,rm_id=rm_id,activity_date=today()); db.session.add(act)
    p=data.get("projection") or {}; act.projected_premium=int(p.get("premium",act.projected_premium or 0)); act.projected_policies=int(p.get("policies",act.projected_policies or 0)); act.projection_remarks=p.get("remarks",act.projection_remarks); act.active_today=bool(data.get("active_today",act.active_today)); act.last_contact_outcome=c.outcome; act.last_contact_at=now_utc(); db.session.flush(); audit("rm.agent_contact","agent_contact",c.id); db.session.commit()
    return jsonify({"contact_id":c.id,"agent_id":aid,"follow_up_required":c.follow_up_required,"follow_up_due_at":c.follow_up_due_at.isoformat() if c.follow_up_due_at else None,"remarks":c.remarks}),201

@bp.post("/projection")
@require_permission("agents:write")
def projection():
    data=request.get_json(silent=True) or {}; rm_id=rm_scope(); aid=data.get("agent_id")
    if not rm_id or not aid: return jsonify({"error":"rm_id_and_agent_id_required"}),400
    a=db.session.get(Agent,aid)
    if not a or a.rm_id!=rm_id: return jsonify({"error":"agent_not_in_rm_scope"}),404
    act=db.session.execute(select(AgentDailyActivity).filter_by(agent_id=aid,activity_date=today())).scalar_one_or_none()
    if not act: act=AgentDailyActivity(agent_id=aid,rm_id=rm_id,activity_date=today()); db.session.add(act)
    act.projected_premium=int(data.get("projected_premium",0)); act.projected_policies=int(data.get("projected_policies",0)); act.active_today=bool(data.get("active_today",False)); act.projection_remarks=data.get("remarks"); audit("rm.agent_projection","agent_daily_activity",act.id); db.session.commit(); return jsonify({"saved":True,"activity_id":act.id})

@bp.post("/hierarchy")
@require_role("RM","MASTER_AGENT","ADMIN")
def hierarchy():
    data=request.get_json(silent=True) or {}; rm_id=rm_scope(); master=data.get("master_agent_id"); sub=data.get("agent_id")
    if not rm_id or not master or not sub: return jsonify({"error":"rm_id_master_agent_id_agent_id_required"}),400
    m=db.session.get(Agent,master); s=db.session.get(Agent,sub)
    if not m or not s or m.rm_id!=rm_id or s.rm_id!=rm_id: return jsonify({"error":"agent_not_in_rm_scope"}),404
    row=db.session.execute(select(AgentHierarchy).filter_by(agent_id=sub)).scalar_one_or_none()
    if not row: row=AgentHierarchy(master_agent_id=master,agent_id=sub,status="active"); db.session.add(row)
    else: row.master_agent_id=master; row.status="active"
    audit("rm.agent_hierarchy","agent_hierarchy",row.id); db.session.commit(); return jsonify({"saved":True,"master_agent_id":master,"agent_id":sub}),201

@bp.post("/business")
@require_permission("policies:write")
def business():
    data=request.get_json(silent=True) or {}; rm_id=rm_scope(); aid=data.get("agent_id")
    if not rm_id or not aid or not data.get("category"): return jsonify({"error":"rm_id_agent_id_category_required"}),400
    a=db.session.get(Agent,aid)
    if not a or a.rm_id!=rm_id: return jsonify({"error":"agent_not_in_rm_scope"}),404
    e=BusinessEvent(rm_id=rm_id,agent_id=aid,business_date=today(),category=data["category"],premium=int(data.get("premium",0)),policies=int(data.get("policies",0)),source=data.get("source","partnershub"),external_reference=data.get("external_reference"),notes=data.get("notes")); db.session.add(e)
    act=db.session.execute(select(AgentDailyActivity).filter_by(agent_id=aid,activity_date=today())).scalar_one_or_none()
    if not act: act=AgentDailyActivity(agent_id=aid,rm_id=rm_id,activity_date=today()); db.session.add(act)
    act.actual_premium=(act.actual_premium or 0)+e.premium; act.actual_policies=(act.actual_policies or 0)+e.policies; act.active_today=True; audit("rm.business_event","business_event",e.id); db.session.commit(); return jsonify({"saved":True,"business_event_id":e.id})

@bp.post("/dispatch")
@require_role("RM","MASTER_AGENT","ADMIN")
def dispatch():
    """Dispatch one RM-priority contact using the existing Twilio/Interakt adapters."""
    data=request.get_json(silent=True) or {}; rm_id=rm_scope(); aid=data.get("agent_id"); channel=data.get("channel","whatsapp")
    if not rm_id or not aid: return jsonify({"error":"rm_id_and_agent_id_required"}),400
    agent=db.session.get(Agent,aid)
    if not agent or agent.rm_id!=rm_id: return jsonify({"error":"agent_not_in_rm_scope"}),404
    blocked=db.session.execute(select(AgentContact).where(AgentContact.rm_id==rm_id,AgentContact.agent_id==aid,AgentContact.contact_date==today(),AgentContact.follow_up_required.is_(False))).first()
    if blocked: return jsonify({"error":"already_contacted_today"}),409
    try:
        if channel=="call":
            from app import is_calling_hours, make_call, get_host, first_name
            if not is_calling_hours(): return jsonify({"error":"calling_hours_9am_to_8pm"}),403
            sid=make_call(agent.phone,f"https://{get_host()}/outbound-handler?aid={agent.partner_code}&name={first_name(agent.name)}")
            if not sid: return jsonify({"error":"call_dispatch_failed"}),502
            reference=sid.sid; outcome="call_dispatched"
        else:
            from app import send_whatsapp
            msg=data.get("message") or f"Namaste {agent.name} ji! Aaj ka business projection share karein. Customer case ho to details bhejiye. - Prashant Sir"
            if not send_whatsapp(agent.phone,msg): return jsonify({"error":"message_dispatch_failed"}),502
            reference=None; outcome="message_dispatched"
        contact_row=AgentContact(rm_id=rm_id,agent_id=aid,contact_date=today(),channel=channel,outcome=outcome,remarks=data.get("remarks"),call_reference=reference,follow_up_required=False); db.session.add(contact_row); db.session.commit()
        return jsonify({"sent":True,"channel":channel,"agent_id":aid,"contact_id":contact_row.id,"reference":reference}),201
    except Exception as exc:
        db.session.rollback(); return jsonify({"error":"dispatch_error","detail":str(exc)}),502

@bp.get("/dashboard")
@require_role("RM","MASTER_AGENT","ADMIN")
def dashboard():
    rm_id=rm_scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    t=target_for(rm_id); agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id,Agent.status=="active")).scalars().all(); acts=db.session.execute(select(AgentDailyActivity).filter_by(rm_id=rm_id,activity_date=today())).scalars().all(); by={x.agent_id:x for x in acts}; events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.business_date==today())).scalars().all(); active=sum(bool(x.active_today) for x in acts); total=sum(x.premium for x in events); policies=sum(x.policies for x in events); high=len({x.agent_id for x in events if x.premium>=t.high_value_threshold}); categories={}
    for e in events: categories[e.category]=categories.get(e.category,0)+e.premium
    return jsonify({"date":str(today()),"rm_id":rm_id,"targets":{"calls":t.call_target,"active_agents":t.active_agent_target,"high_value_agents":t.high_value_agent_target,"high_value_threshold":t.high_value_threshold},"progress":{"active_agents":active,"active_gap":max(t.active_agent_target-active,0),"daily_business":total,"daily_policies":policies,"high_value_agents":high,"high_value_gap":max(t.high_value_agent_target-high,0),"category_business":categories},"agents":[{"agent_id":a.id,"partner_code":a.partner_code,"name":a.name,"master_agent_id":db.session.execute(select(AgentHierarchy.master_agent_id).filter_by(agent_id=a.id,status="active")).scalar_one_or_none(),"active_today":bool(by[a.id].active_today) if a.id in by else False,"projected_premium":by[a.id].projected_premium if a.id in by else 0,"actual_premium":by[a.id].actual_premium if a.id in by else 0,"actual_policies":by[a.id].actual_policies if a.id in by else 0,"remarks":by[a.id].projection_remarks if a.id in by else None} for a in agents]})

@bp.post("/reconciliation")
@require_role("RM","MASTER_AGENT","ADMIN")
def reconcile():
    data=request.get_json(silent=True) or {}; rm_id=rm_scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    st=int(data.get("source_total",0)); sp=int(data.get("source_policies",0)); yt=int(data.get("system_total",0)); yp=int(data.get("system_policies",0)); d=st-yt; dp=sp-yp; status="matched" if d==0 and dp==0 else "mismatch"; row=db.session.execute(select(BusinessReconciliation).filter_by(rm_id=rm_id,reconciliation_date=today())).scalar_one_or_none()
    if not row: row=BusinessReconciliation(rm_id=rm_id,reconciliation_date=today()); db.session.add(row)
    row.source_total=st; row.source_policies=sp; row.system_total=yt; row.system_policies=yp; row.difference=d; row.policy_difference=dp; row.status=status; row.source_name=data.get("source_name","external_import"); row.notes=data.get("notes"); audit("rm.reconciliation","business_reconciliation",row.id); db.session.commit(); return jsonify({"status":status,"difference":d,"policy_difference":dp})

@bp.get("/contacts/export.csv")
@require_role("RM","MASTER_AGENT","ADMIN")
def export_contacts():
    rm_id=rm_scope()
    if not rm_id: return Response("rm_mapping_required\n",status=422,mimetype="text/plain")
    rows=db.session.execute(select(AgentContact,Agent.partner_code,Agent.name,Agent.phone).join(Agent,Agent.id==AgentContact.agent_id).where(AgentContact.rm_id==rm_id).order_by(AgentContact.created_at.desc())).all(); out=io.StringIO(); w=csv.writer(out); w.writerow(["contact_id","date","partner_code","agent_name","phone","channel","outcome","follow_up_required","follow_up_due_at","remarks","call_reference"])
    for c,code,name,phone in rows: w.writerow([c.id,c.contact_date,code,name,phone,c.channel,c.outcome,c.follow_up_required,c.follow_up_due_at.isoformat() if c.follow_up_due_at else "",c.remarks or "",c.call_reference or ""])
    return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":f"attachment; filename=rm_contacts_{today()}.csv"})
