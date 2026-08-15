"""P11 scheduler bridge and RM BI APIs."""
import json
import uuid
from datetime import datetime, timedelta, timezone, date
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, AuditLog, RM
from .models_p4 import BusinessEvent
from .models_p7 import RMDailyBusinessTarget, AgentDailyMessage
from .models_p10 import RenewalWorkflow, RenewalReminder, FollowUpTask, FollowUpEvent
from .models_p11 import AutomationRun, RMDailyBISnapshot
from .security import current_user, require_role

bp = Blueprint("p11", __name__, url_prefix="/api/p11")

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
    u=current_user()
    db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid, user_id=u.id if u else None, request_id=str(uuid.uuid4()), ip_address=request.remote_addr))

def start_run(run_type, key):
    existing=db.session.execute(select(AutomationRun).filter_by(run_key=key)).scalar_one_or_none()
    if existing:
        return existing, False
    run=AutomationRun(run_key=key, run_type=run_type, status="running")
    db.session.add(run); db.session.flush()
    return run, True

@bp.post("/run")
@require_role("ADMIN","MASTER_AGENT","RM")
def run_automation():
    data=request.get_json(silent=True) or {}
    rm_id=scope()
    run_type=data.get("type","renewal_reminders")
    key=f"{run_type}:{data.get('date', now().date().isoformat())}:{rm_id or 'global'}"
    run,created=start_run(run_type,key)
    if not created:
        return jsonify({"run_id":run.id,"status":run.status,"reused":True}),200
    processed=created_count=failed=0
    try:
        if run_type == "renewal_reminders":
            horizon=now()+timedelta(days=15)
            q=select(RenewalWorkflow).where(RenewalWorkflow.status=="open", RenewalWorkflow.expiry_at<=horizon)
            if rm_id: q=q.where(RenewalWorkflow.agent_id.in_(select(Agent.id).where(Agent.rm_id==rm_id)))
            renewals=db.session.execute(q).scalars().all()
            for renewal in renewals:
                days=max(0,(renewal.expiry_at.date()-now().date()).days)
                reminder_day=15 if days<=15 and days>5 else (5 if days<=5 and days>1 else (1 if days<=1 else None))
                if reminder_day is None: continue
                processed+=1
                for recipient_type in ("agent","customer"):
                    key2=f"renewal:{renewal.id}:{reminder_day}:{recipient_type}"
                    exists=db.session.execute(select(RenewalReminder).filter_by(dedupe_key=key2)).scalar_one_or_none()
                    if exists: continue
                    rr=RenewalReminder(renewal_id=renewal.id, reminder_day=reminder_day, scheduled_at=now(), channel="whatsapp", recipient_type=recipient_type, status="queued", dedupe_key=key2)
                    db.session.add(rr); db.session.flush()
                    audit("renewal.reminder.queued","renewal_reminder",rr.id); created_count+=1
        elif run_type == "followups":
            q=select(FollowUpTask).where(FollowUpTask.status=="open", FollowUpTask.due_at<=now())
            if rm_id: q=q.where(FollowUpTask.rm_id==rm_id)
            for task in db.session.execute(q).scalars().all():
                processed+=1
                event=FollowUpEvent(task_id=task.id,event_type="due",channel="system",payload_json=json.dumps({"due_at":task.due_at.isoformat()}))
                db.session.add(event)
                audit("follow_up.due","follow_up_task",task.id)
        elif run_type == "message_queue":
            q=select(AgentDailyMessage).where(AgentDailyMessage.status=="queued")
            for message in db.session.execute(q).scalars().all():
                processed+=1
                message.status="ready_for_dispatch"
        else:
            raise ValueError("unsupported_run_type")
        run.processed=processed; run.created=created_count; run.failed=failed; run.status="completed"; run.completed_at=now(); db.session.commit()
    except Exception as exc:
        db.session.rollback()
        run=db.session.get(AutomationRun,run.id); run.status="failed"; run.error=str(exc); run.completed_at=now(); db.session.commit()
        return jsonify({"run_id":run.id,"status":"failed","error":str(exc)}),500
    return jsonify({"run_id":run.id,"status":run.status,"processed":processed,"created":created_count,"failed":failed})

@bp.post("/bi/snapshot")
@require_role("ADMIN","MASTER_AGENT","RM")
def bi_snapshot():
    rm_id=scope()
    if not rm_id: return jsonify({"error":"rm_mapping_required"}),422
    day=date.today(); start=datetime.combine(day,datetime.min.time(),tzinfo=timezone.utc); end=start+timedelta(days=1)
    events=db.session.execute(select(BusinessEvent).where(BusinessEvent.rm_id==rm_id,BusinessEvent.business_date>=day,BusinessEvent.business_date<end)).scalars().all()
    actual=sum(e.premium for e in events)
    renewal=sum(e.premium for e in events if str(e.category).lower()=="renewal")
    newbiz=actual-renewal
    active_agents=db.session.scalar(select(func.count(Agent.id)).where(Agent.rm_id==rm_id,Agent.status=="active")) or 0
    target=db.session.execute(select(RMDailyBusinessTarget).filter_by(rm_id=rm_id,target_date=day)).scalar_one_or_none()
    target_value=target.target_premium if target else 500000
    existing_meetings=0; new_meetings=0
    try:
        from .models_p5 import RMVisitPlan
        plans=db.session.execute(select(RMVisitPlan).where(RMVisitPlan.rm_id==rm_id,RMVisitPlan.visit_date==day)).scalars().all()
        existing_meetings=sum(1 for p in plans if p.plan_type=="existing"); new_meetings=sum(1 for p in plans if p.plan_type=="new")
    except Exception: pass
    try:
        from .models_p4 import AgentDailyActivity
        calls=db.session.scalar(select(func.count(AgentDailyActivity.id)).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==day,AgentDailyActivity.call_outcome.is_not(None))) or 0
        projected=db.session.scalar(select(func.coalesce(func.sum(AgentDailyActivity.projected_premium),0)).where(AgentDailyActivity.rm_id==rm_id,AgentDailyActivity.activity_date==day)) or 0
    except Exception:
        calls=0; projected=0
    pending=db.session.scalar(select(func.count(FollowUpTask.id)).where(FollowUpTask.rm_id==rm_id,FollowUpTask.status=="open",FollowUpTask.due_at<=now())) or 0
    high_value=db.session.scalar(select(func.count(Agent.id)).where(Agent.rm_id==rm_id,Agent.status=="active")) or 0
    snap=db.session.execute(select(RMDailyBISnapshot).filter_by(rm_id=rm_id,business_date=start)).scalar_one_or_none()
    if not snap: snap=RMDailyBISnapshot(rm_id=rm_id,business_date=start); db.session.add(snap)
    snap.premium_actual=actual; snap.premium_projected=int(projected); snap.renewal_premium=renewal; snap.new_business_premium=newbiz; snap.active_agents=active_agents; snap.existing_meetings=existing_meetings; snap.new_meetings=new_meetings; snap.calls_completed=calls; snap.pending_followups=pending; snap.high_value_agents=high_value; snap.target_premium=target_value
    audit("rm.bi.snapshot","rm_daily_bi_snapshot",snap.id); db.session.commit()
    return jsonify({"date":day.isoformat(),"actual":actual,"projected":int(projected),"renewal":renewal,"new_business":newbiz,"active_agents":active_agents,"meetings":{"existing":existing_meetings,"new":new_meetings},"calls":calls,"pending_followups":pending,"target":target_value,"gap":max(target_value-actual,0)})

@bp.get("/bi/dashboard")
@require_role("ADMIN","MASTER_AGENT","RM")
def bi_dashboard():
    rm_id=scope()
    if not rm_id:return jsonify({"error":"rm_mapping_required"}),422
    rows=db.session.execute(select(RMDailyBISnapshot).where(RMDailyBISnapshot.rm_id==rm_id).order_by(RMDailyBISnapshot.business_date.desc()).limit(30)).scalars().all()
    return jsonify({"items":[{"date":r.business_date.date().isoformat(),"actual":r.premium_actual,"projected":r.premium_projected,"renewal":r.renewal_premium,"new_business":r.new_business_premium,"active_agents":r.active_agents,"existing_meetings":r.existing_meetings,"new_meetings":r.new_meetings,"high_value_agents":r.high_value_agents,"calls":r.calls_completed,"pending_followups":r.pending_followups,"target":r.target_premium,"gap":max(r.target_premium-r.premium_actual,0)} for r in rows]})
