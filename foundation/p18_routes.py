"""P18 campaign automation and inbox next-action orchestration."""
from datetime import datetime, timezone
import uuid

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from .db import db
from .models import Agent, AuditLog
from .models_p7 import AgentDailyMessage
from .models_p18 import MessagingCampaign, CampaignRecipient, InboxAction
from .security import current_user, require_auth, require_role

bp = Blueprint("p18_campaigns", __name__, url_prefix="/api/p18")


def now():
    return datetime.now(timezone.utc)


def audit(action, kind, rid=None):
    u = current_user()
    db.session.add(AuditLog(action=action, resource_type=kind, resource_id=rid, user_id=u.id if u else None, request_id=str(uuid.uuid4()), ip_address=request.remote_addr))


def render(template, agent):
    replacements = {
        "{{agent_name}}": agent.name or "Agent",
        "{{partner_code}}": agent.partner_code or "",
    }
    text = template
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


@bp.post("/campaigns")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def create_campaign():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    template = str(data.get("message_template", "")).strip()
    if not name or not template:
        return jsonify({"error": "name_and_message_template_required"}), 400
    channel = str(data.get("channel", "whatsapp")).lower()
    if channel != "whatsapp":
        return jsonify({"error": "unsupported_channel"}), 400
    user = current_user()
    row = MessagingCampaign(rm_id=data.get("rm_id"), name=name, channel=channel, message_template=template, status="draft", scheduled_at=None, created_by=user.id)
    db.session.add(row)
    db.session.flush()
    audit("p18.campaign.create", "messaging_campaign", row.id)
    db.session.commit()
    return jsonify({"id": row.id, "status": row.status}), 201


@bp.post("/campaigns/<campaign_id>/recipients")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def add_recipients(campaign_id):
    campaign = db.session.get(MessagingCampaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign_not_found"}), 404
    data = request.get_json(silent=True) or {}
    agent_ids = data.get("agent_ids") or []
    if not isinstance(agent_ids, list) or not agent_ids:
        return jsonify({"error": "agent_ids_required"}), 400
    added = 0
    for agent_id in agent_ids[:500]:
        agent = db.session.get(Agent, agent_id)
        if not agent:
            continue
        existing = db.session.execute(select(CampaignRecipient).filter_by(campaign_id=campaign_id, agent_id=agent_id)).scalar_one_or_none()
        if existing:
            continue
        db.session.add(CampaignRecipient(campaign_id=campaign_id, agent_id=agent_id, status="pending"))
        added += 1
    db.session.commit()
    return jsonify({"campaign_id": campaign_id, "added": added})


@bp.get("/campaigns/<campaign_id>")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def campaign_detail(campaign_id):
    campaign = db.session.get(MessagingCampaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign_not_found"}), 404
    recipients = db.session.execute(select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id).order_by(CampaignRecipient.created_at.asc())).scalars().all()
    return jsonify({
        "id": campaign.id,
        "name": campaign.name,
        "channel": campaign.channel,
        "status": campaign.status,
        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
        "recipients": [{"id": r.id, "agent_id": r.agent_id, "status": r.status, "queued_message_id": r.queued_message_id} for r in recipients],
    })


@bp.post("/campaigns/<campaign_id>/queue")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def queue_campaign(campaign_id):
    campaign = db.session.get(MessagingCampaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign_not_found"}), 404
    if campaign.status == "cancelled":
        return jsonify({"error": "campaign_cancelled"}), 409
    recipients = db.session.execute(select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id, CampaignRecipient.status == "pending")).scalars().all()
    queued = skipped = 0
    for recipient in recipients:
        agent = db.session.get(Agent, recipient.agent_id)
        if not agent:
            recipient.status = "failed"; recipient.error_message = "agent_not_found"; skipped += 1; continue
        body = render(campaign.message_template, agent)
        dedupe = f"p18:campaign:{campaign.id}:agent:{agent.id}"
        existing = db.session.execute(select(AgentDailyMessage).filter_by(dedupe_key=dedupe)).scalar_one_or_none()
        if existing:
            recipient.status = "queued"; recipient.queued_message_id = existing.id; skipped += 1; continue
        message = AgentDailyMessage(rm_id=campaign.rm_id or agent.rm_id, agent_id=agent.id, message_date=now().date(), channel="whatsapp", message_type="campaign", body=body, status="queued", dedupe_key=dedupe)
        db.session.add(message)
        db.session.flush()
        recipient.status = "queued"; recipient.rendered_message = body; recipient.queued_message_id = message.id
        queued += 1
    campaign.status = "queued" if queued or skipped else "completed"
    audit("p18.campaign.queue", "messaging_campaign", campaign.id)
    db.session.commit()
    return jsonify({"campaign_id": campaign.id, "queued": queued, "already_queued": skipped, "status": campaign.status})


@bp.post("/campaigns/<campaign_id>/cancel")
@require_role("RM", "MASTER_AGENT", "ADMIN")
def cancel_campaign(campaign_id):
    campaign = db.session.get(MessagingCampaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign_not_found"}), 404
    campaign.status = "cancelled"
    audit("p18.campaign.cancel", "messaging_campaign", campaign.id)
    db.session.commit()
    return jsonify({"id": campaign.id, "status": campaign.status})


@bp.post("/inbox-actions")
@require_auth
def create_inbox_action():
    data = request.get_json(silent=True) or {}
    thread_id = str(data.get("thread_id", "")).strip()
    action_type = str(data.get("action_type", "")).strip()
    if not thread_id or not action_type:
        return jsonify({"error": "thread_id_and_action_type_required"}), 400
    user = current_user()
    row = InboxAction(thread_id=thread_id, agent_id=data.get("agent_id"), action_type=action_type, suggested_text=data.get("suggested_text"), requires_human_approval=bool(data.get("requires_human_approval", True)), status="open", created_by=user.id)
    db.session.add(row)
    db.session.flush()
    audit("p18.inbox_action.create", "inbox_action", row.id)
    db.session.commit()
    return jsonify({"id": row.id, "status": row.status, "requires_human_approval": row.requires_human_approval}), 201


@bp.get("/inbox-actions")
@require_role("AGENT", "RM", "MASTER_AGENT", "ADMIN")
def list_inbox_actions():
    status = request.args.get("status", "open")
    q = select(InboxAction).where(InboxAction.status == status).order_by(InboxAction.created_at.desc()).limit(200)
    rows = db.session.execute(q).scalars().all()
    return jsonify({"items": [{"id": r.id, "thread_id": r.thread_id, "agent_id": r.agent_id, "action_type": r.action_type, "suggested_text": r.suggested_text, "requires_human_approval": r.requires_human_approval, "status": r.status} for r in rows]})


@bp.post("/inbox-actions/<action_id>/complete")
@require_auth
def complete_inbox_action(action_id):
    row = db.session.get(InboxAction, action_id)
    if not row:
        return jsonify({"error": "inbox_action_not_found"}), 404
    data = request.get_json(silent=True) or {}
    row.status = "completed"
    row.outcome = data.get("outcome")
    row.completed_at = now()
    audit("p18.inbox_action.complete", "inbox_action", row.id)
    db.session.commit()
    return jsonify({"id": row.id, "status": row.status, "outcome": row.outcome})
