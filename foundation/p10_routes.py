"""P10 persistent follow-up and renewal workflow APIs."""
from datetime import date, datetime, timedelta, timezone
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy import func, select
from .db import db
from .models import Agent, Customer, Lead, Policy, RM, AuditLog
from .models_p10 import RenewalWorkflow, RenewalReminder, FollowUpTask, FollowUpEvent
from .security import current_user, require_role, require_permission

bp = Blueprint("p10", __name__, url_prefix="/api/p10")


def now():
    return datetime.now(timezone.utc)


def audit(action, kind, rid=None):
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid,
                            user_id=u.id if u else None, request_id=str(uuid.uuid4()),
                            ip_address=request.remote_addr))


def dt(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None


def rm_scope():
    u = current_user()
    requested = request.args.get("rm_id") or (request.get_json(silent=True) or {}).get("rm_id")
    if not u:
        return None
    rm = db.session.execute(select(RM).filter(func.lower(RM.email) == func.lower(u.email))).scalar_one_or_none()
    admin = any(r.name == "ADMIN" for r in getattr(u, "roles", []))
    if requested and rm and requested != rm.id and not admin:
        return None
    return requested or (rm.id if rm else None)


@bp.post("/renewals")
@require_permission("renewals:write")
def create_renewal():
    data = request.get_json(silent=True) or {}
    if not data.get("policy_id") or not data.get("customer_id") or not data.get("agent_id") or not data.get("expiry_at"):
        return jsonify({"error": "policy_id_customer_id_agent_id_expiry_at_required"}), 400
    existing = db.session.execute(select(RenewalWorkflow).filter_by(policy_id=data["policy_id"])).scalar_one_or_none()
    if existing:
        return jsonify({"error": "renewal_workflow_exists", "id": existing.id}), 409
    expiry = dt(data["expiry_at"])
    workflow = RenewalWorkflow(policy_id=data["policy_id"], customer_id=data["customer_id"], agent_id=data["agent_id"], expiry_at=expiry, stage=data.get("stage", "pending"), status="open", notes=data.get("notes"))
    db.session.add(workflow); db.session.flush()
    for days in (15, 5, 1):
        scheduled = expiry - timedelta(days=days)
        for recipient in ("agent", "customer"):
            key = f"{workflow.id}:{days}:{recipient}:whatsapp"
            db.session.add(RenewalReminder(renewal_id=workflow.id, reminder_day=days, scheduled_at=scheduled, channel="whatsapp", recipient_type=recipient, status="queued", dedupe_key=key))
    task = FollowUpTask(renewal_id=workflow.id, agent_id=data["agent_id"], task_type="renewal_initial", priority=90, due_at=max(now(), expiry - timedelta(days=15)), status="open")
    db.session.add(task); db.session.flush(); audit("renewal.create", "renewal_workflow", workflow.id); db.session.commit()
    return jsonify({"renewal_id": workflow.id, "reminders": 6, "initial_task_id": task.id}), 201


@bp.get("/renewals")
@require_role("AGENT", "RM", "MASTER_AGENT", "ADMIN")
def list_renewals():
    q = select(RenewalWorkflow).order_by(RenewalWorkflow.expiry_at.asc()).limit(200)
    rows = db.session.execute(q).scalars().all()
    return jsonify({"items": [{"id": r.id, "policy_id": r.policy_id, "customer_id": r.customer_id, "agent_id": r.agent_id, "expiry_at": r.expiry_at.isoformat(), "stage": r.stage, "status": r.status, "next_action_at": r.next_action_at.isoformat() if r.next_action_at else None} for r in rows]})


@bp.post("/renewals/<renewal_id>/status")
@require_permission("renewals:write")
def renewal_status(renewal_id):
    r = db.session.get(RenewalWorkflow, renewal_id)
    if not r:
        return jsonify({"error": "renewal_not_found"}), 404
    data = request.get_json(silent=True) or {}
    r.stage = data.get("stage", r.stage)
    r.status = data.get("status", r.status)
    r.last_contact_at = dt(data.get("last_contact_at")) or r.last_contact_at
    r.next_action_at = dt(data.get("next_action_at")) or r.next_action_at
    r.notes = data.get("notes", r.notes)
    if r.status == "renewed":
        r.renewed_at = dt(data.get("renewed_at")) or now()
        r.renewed_premium = int(data.get("renewed_premium", r.renewed_premium or 0))
    audit("renewal.status.update", "renewal_workflow", r.id); db.session.commit()
    return jsonify({"saved": True, "status": r.status, "stage": r.stage})


@bp.get("/reminders/due")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def due_reminders():
    rm_id = rm_scope()
    q = select(RenewalReminder).join(RenewalWorkflow, RenewalWorkflow.id == RenewalReminder.renewal_id).join(Agent, Agent.id == RenewalWorkflow.agent_id)
    q = q.where(RenewalReminder.status == "queued", RenewalReminder.scheduled_at <= now())
    if rm_id:
        q = q.where(Agent.rm_id == rm_id)
    rows = db.session.execute(q.order_by(RenewalReminder.scheduled_at.asc()).limit(200)).scalars().all()
    return jsonify({"items": [{"id": x.id, "renewal_id": x.renewal_id, "day": x.reminder_day, "recipient_type": x.recipient_type, "channel": x.channel, "scheduled_at": x.scheduled_at.isoformat()} for x in rows]})


@bp.post("/reminders/<reminder_id>/dispatch-state")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def reminder_dispatch_state(reminder_id):
    row = db.session.get(RenewalReminder, reminder_id)
    if not row:
        return jsonify({"error": "reminder_not_found"}), 404
    data = request.get_json(silent=True) or {}
    row.status = data.get("status", row.status)
    row.provider_reference = data.get("provider_reference", row.provider_reference)
    row.sent_at = dt(data.get("sent_at")) or (now() if row.status in {"sent", "delivered", "read"} else row.sent_at)
    row.error_message = data.get("error_message", row.error_message)
    audit("renewal.reminder.status", "renewal_reminder", row.id); db.session.commit()
    return jsonify({"saved": True, "status": row.status})


@bp.post("/follow-ups")
@require_permission("leads:write")
def create_followup():
    data = request.get_json(silent=True) or {}
    if not data.get("task_type") or not data.get("due_at"):
        return jsonify({"error": "task_type_and_due_at_required"}), 400
    task = FollowUpTask(lead_id=data.get("lead_id"), renewal_id=data.get("renewal_id"), agent_id=data.get("agent_id"), rm_id=data.get("rm_id"), task_type=data["task_type"], priority=int(data.get("priority", 50)), due_at=dt(data["due_at"]), status="open", remarks=data.get("remarks"))
    db.session.add(task); db.session.flush(); audit("follow_up.create", "follow_up_task", task.id); db.session.commit()
    return jsonify({"id": task.id, "status": task.status}), 201


@bp.get("/follow-ups/due")
@require_role("AGENT", "RM", "MASTER_AGENT", "ADMIN")
def due_followups():
    rm_id = rm_scope()
    q = select(FollowUpTask).where(FollowUpTask.status == "open", FollowUpTask.due_at <= now())
    if rm_id:
        q = q.where(FollowUpTask.rm_id == rm_id)
    rows = db.session.execute(q.order_by(FollowUpTask.priority.desc(), FollowUpTask.due_at.asc()).limit(200)).scalars().all()
    return jsonify({"items": [{"id": x.id, "lead_id": x.lead_id, "renewal_id": x.renewal_id, "agent_id": x.agent_id, "task_type": x.task_type, "priority": x.priority, "due_at": x.due_at.isoformat(), "remarks": x.remarks} for x in rows]})


@bp.post("/follow-ups/<task_id>/complete")
@require_permission("leads:write")
def complete_followup(task_id):
    task = db.session.get(FollowUpTask, task_id)
    if not task:
        return jsonify({"error": "follow_up_not_found"}), 404
    data = request.get_json(silent=True) or {}
    task.status = data.get("status", "completed")
    task.completed_at = now()
    task.outcome = data.get("outcome")
    task.remarks = data.get("remarks", task.remarks)
    db.session.add(FollowUpEvent(task_id=task.id, event_type="completed", channel=data.get("channel"), provider_reference=data.get("provider_reference"), payload_json=data.get("payload_json")))
    if task.renewal_id and data.get("next_due_at"):
        next_task = FollowUpTask(renewal_id=task.renewal_id, agent_id=task.agent_id, rm_id=task.rm_id, task_type="renewal_follow_up", priority=task.priority, due_at=dt(data["next_due_at"]), status="open")
        db.session.add(next_task)
    audit("follow_up.complete", "follow_up_task", task.id); db.session.commit()
    return jsonify({"completed": True, "outcome": task.outcome})


@bp.get("/dashboard")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def dashboard():
    rm_id = rm_scope()
    if not rm_id:
        return jsonify({"error": "rm_mapping_required"}), 422
    renewals = db.session.execute(select(RenewalWorkflow).join(Agent, Agent.id == RenewalWorkflow.agent_id).where(Agent.rm_id == rm_id)).scalars().all()
    tasks = db.session.execute(select(FollowUpTask).where(FollowUpTask.rm_id == rm_id, FollowUpTask.status == "open", FollowUpTask.due_at <= now())).scalars().all()
    due_15 = sum(1 for r in renewals if r.status == "open" and 0 < (r.expiry_at - now()).total_seconds() <= 15 * 86400)
    due_5 = sum(1 for r in renewals if r.status == "open" and 0 < (r.expiry_at - now()).total_seconds() <= 5 * 86400)
    due_1 = sum(1 for r in renewals if r.status == "open" and 0 < (r.expiry_at - now()).total_seconds() <= 86400)
    renewed = sum(1 for r in renewals if r.status == "renewed")
    premium = sum(r.renewed_premium for r in renewals if r.status == "renewed")
    return jsonify({"renewals_total": len(renewals), "due_15_days": due_15, "due_5_days": due_5, "due_1_day": due_1, "open_followups": len(tasks), "renewed": renewed, "renewed_premium": premium})
