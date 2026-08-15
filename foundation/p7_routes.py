"""RM daily business target, marketing strategy and automatic agent-message APIs."""
from datetime import date, datetime, timezone
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, AuditLog, RM
from .models_p4 import BusinessEvent
from .models_p7 import RMDailyBusinessTarget, RMMarketingPlan, AgentDailyMessage
from .security import current_user, require_role

bp = Blueprint("p7", __name__, url_prefix="/api/p7")


def today(): return date.today()
def now(): return datetime.now(timezone.utc)
def rm_for_user():
    u = current_user()
    if not u: return None
    return db.session.execute(select(RM).filter(func.lower(RM.email) == func.lower(u.email))).scalar_one_or_none()
def scope():
    req = request.args.get("rm_id") or (request.get_json(silent=True) or {}).get("rm_id")
    rm = rm_for_user(); admin = any(r.name == "ADMIN" for r in getattr(current_user(), "roles", []))
    if req and rm and req != rm.id and not admin: return None
    return req or (rm.id if rm else None)
def audit(action, kind, rid=None):
    u=current_user(); db.session.add(AuditLog(action=action,resource_type=kind,resource_id=rid,user_id=u.id if u else None,request_id=str(uuid.uuid4()),ip_address=request.remote_addr))


def get_target(rm_id, d=None):
    d = d or today()
    row = db.session.execute(select(RMDailyBusinessTarget).filter_by(rm_id=rm_id,target_date=d)).scalar_one_or_none()
    if not row:
        row=RMDailyBusinessTarget(rm_id=rm_id,target_date=d,min_premium=300000,target_premium=500000,stretch_premium=500000)
        db.session.add(row); db.session.flush()
    return row

@bp.get("/target")
@require_role("RM","MASTER_AGENT","ADMIN")
def target():
    rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    t=get_target(rm_id)
    return jsonify({"date":str(t.target_date),"min":t.min_premium,"target":t.target_premium,"stretch":t.stretch_premium,"projected":t.projected_premium,"actual":t.actual_premium,"gap_to_target":max(t.target_premium-(t.actual_premium+t.projected_premium),0),"achievement_pct":round((t.actual_premium/max(t.target_premium,1))*100,2)})

@bp.post("/target")
@require_role("RM","MASTER_AGENT","ADMIN")
def set_target():
    data=request.get_json(silent=True) or {}; rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    t=get_target(rm_id,date.fromisoformat(data.get("date")) if data.get("date") else today())
    t.min_premium=int(data.get("min_premium",t.min_premium)); t.target_premium=int(data.get("target_premium",t.target_premium)); t.stretch_premium=int(data.get("stretch_premium",t.stretch_premium)); audit("rm.target.update","rm_daily_business_target",t.id); db.session.commit(); return jsonify({"saved":True})

@bp.get("/dashboard")
@require_role("RM","MASTER_AGENT","ADMIN")
def dashboard():
    rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    t=get_target(rm_id); events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.business_date==today())).scalars().all()
    actual=sum(e.premium for e in events); projected=sum((__import__('foundation.models_p4',fromlist=['AgentDailyActivity']).AgentDailyActivity.projected_premium) if False else 0 for _ in [])
    t.actual_premium=actual; db.session.commit()
    bycat={}
    for e in events: bycat[e.category]=bycat.get(e.category,0)+e.premium
    return jsonify({"date":str(today()),"target":t.target_premium,"minimum":t.min_premium,"actual":actual,"gap":max(t.target_premium-actual,0),"achievement_pct":round(actual/max(t.target_premium,1)*100,2),"category_business":bycat})

@bp.post("/marketing-plan")
@require_role("RM","MASTER_AGENT","ADMIN")
def marketing_plan():
    data=request.get_json(silent=True) or {}; rm_id=scope()
    if not rm_id or not data.get("segment") or not data.get("objective") or not data.get("message_template"):
        return jsonify({"error":"rm_mapping_segment_objective_message_required"}),400
    p=RMMarketingPlan(rm_id=rm_id,plan_date=date.fromisoformat(data.get("date")) if data.get("date") else today(),channel=data.get("channel","whatsapp"),segment=data["segment"],objective=data["objective"],message_template=data["message_template"],scheduled_time=data.get("scheduled_time"),is_active=True)
    db.session.add(p); db.session.flush(); audit("rm.marketing_plan.create","rm_marketing_plan",p.id); db.session.commit(); return jsonify({"saved":True,"id":p.id}),201

@bp.get("/marketing-plan")
@require_role("RM","MASTER_AGENT","ADMIN")
def list_marketing():
    rm_id=scope()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    rows=db.session.execute(select(RMMarketingPlan).where(RMMarketingPlan.rm_id==rm_id,RMMarketingPlan.plan_date==today(),RMMarketingPlan.is_active.is_(True))).scalars().all()
    return jsonify({"items":[{"id":r.id,"channel":r.channel,"segment":r.segment,"objective":r.objective,"message_template":r.message_template,"scheduled_time":r.scheduled_time} for r in rows]})

@bp.post("/messages/queue")
@require_role("RM","MASTER_AGENT","ADMIN")
def queue_messages():
    data=request.get_json(silent=True) or {}; rm_id=scope(); d=date.fromisoformat(data.get("date")) if data.get("date") else today()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    agents=db.session.execute(select(Agent).where(Agent.rm_id==rm_id,Agent.status=="active")).scalars().all(); msg_type=data.get("message_type","daily_target"); channel=data.get("channel","whatsapp"); template=data.get("message_template")
    if not template:return jsonify({"error":"message_template_required"}),400
    created=[]
    for a in agents:
        body=template.replace("{{agent_name}}",a.name).replace("{{target}}",f"₹{get_target(rm_id,d).target_premium:,}").replace("{{minimum}}",f"₹{get_target(rm_id,d).min_premium:,}")
        key=f"{a.id}:{d}:{channel}:{msg_type}"
        if db.session.execute(select(AgentDailyMessage).filter_by(dedupe_key=key)).scalar_one_or_none(): continue
        row=AgentDailyMessage(rm_id=rm_id,agent_id=a.id,message_date=d,channel=channel,message_type=msg_type,body=body,dedupe_key=key)
        db.session.add(row); created.append(row)
    for r in created: audit("agent.message.queued","agent_daily_message",r.id)
    db.session.commit(); return jsonify({"queued":len(created),"date":str(d),"channel":channel,"message_type":msg_type})
